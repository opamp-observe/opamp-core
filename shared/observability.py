# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared OpenTelemetry configuration parsing and runtime wiring helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from quart import Quart

CFG_OTLP_ENDPOINTS = "otlp-endpoints"
CFG_OTLP_ALL = "ALL"
CFG_OTLP_ALL_FALLBACK = "all"
CFG_OTLP_LOGS = "logs"
CFG_OTLP_METRICS = "metrics"
CFG_OTLP_TRACES = "traces"
CFG_OTLP_EXPORT_INTERVAL = "export_interval"
DEFAULT_EXPORT_INTERVAL_SECONDS = 300
APP_EXTENSION_OBSERVABILITY_ENABLED = "shared:observability_enabled"
APP_EXTENSION_REQUEST_COUNTER_ENABLED = "shared:observability_request_counter_enabled"
APP_EXTENSION_ASGI_MIDDLEWARE_ENABLED = "shared:observability_asgi_middleware_enabled"

LOGGER = logging.getLogger(__name__)

_LOGGING_ENABLED = False
_METRICS_ENABLED = False
_TRACING_ENABLED = False
_ACTIVE_SERVICE_NAME: str | None = None


@dataclass(frozen=True)
class ObservabilityConfig:
    """Normalized OTLP endpoint settings shared across OpAMP runtimes.

    Why this structure exists:
    keeping one normalized config object prevents each runtime from inventing
    slightly different precedence rules for `ALL`, per-signal overrides, and
    export interval handling.
    """

    all_endpoint: str | None = None
    logs_endpoint: str | None = None
    metrics_endpoint: str | None = None
    traces_endpoint: str | None = None
    export_interval_seconds: int = DEFAULT_EXPORT_INTERVAL_SECONDS

    @property
    def resolved_logs_endpoint(self) -> str | None:
        """Return the effective logs endpoint after applying `ALL` fallback."""
        return self.logs_endpoint or self.all_endpoint

    @property
    def resolved_metrics_endpoint(self) -> str | None:
        """Return the effective metrics endpoint after applying `ALL` fallback."""
        return self.metrics_endpoint or self.all_endpoint

    @property
    def resolved_traces_endpoint(self) -> str | None:
        """Return the effective traces endpoint after applying `ALL` fallback."""
        return self.traces_endpoint or self.all_endpoint

    def enabled(self) -> bool:
        """Return whether any OTLP endpoint is configured for this runtime."""
        return any(
            endpoint
            for endpoint in (
                self.all_endpoint,
                self.logs_endpoint,
                self.metrics_endpoint,
                self.traces_endpoint,
            )
        )


def _coerce_positive_int(value: Any, default: int) -> int:
    """Return a positive integer value or the supplied default."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def _coerce_optional_text(value: Any) -> str | None:
    """Normalize optional config text values to a stripped string or `None`."""
    normalized = str(value or "").strip()
    return normalized or None


def load_observability_config_from_payload(
    payload: dict[str, Any] | None,
) -> ObservabilityConfig:
    """Return normalized OTLP settings from a raw JSON-style config payload.

    Why this helper exists:
    most runtimes load larger config payloads first and then need a predictable
    way to extract the shared top-level `otlp-endpoints` section.
    """
    raw = payload if isinstance(payload, dict) else {}
    observability_raw = raw.get(CFG_OTLP_ENDPOINTS, {})
    if not isinstance(observability_raw, dict):
        observability_raw = {}
    all_endpoint = _coerce_optional_text(
        observability_raw.get(CFG_OTLP_ALL, observability_raw.get(CFG_OTLP_ALL_FALLBACK))
    )
    return ObservabilityConfig(
        all_endpoint=all_endpoint,
        logs_endpoint=_coerce_optional_text(observability_raw.get(CFG_OTLP_LOGS)),
        metrics_endpoint=_coerce_optional_text(observability_raw.get(CFG_OTLP_METRICS)),
        traces_endpoint=_coerce_optional_text(observability_raw.get(CFG_OTLP_TRACES)),
        export_interval_seconds=_coerce_positive_int(
            observability_raw.get(CFG_OTLP_EXPORT_INTERVAL),
            DEFAULT_EXPORT_INTERVAL_SECONDS,
        ),
    )


def _warn_if_service_name_changes(service_name: str) -> None:
    """Warn when one process tries to rebind observability to a new service name.

    Why this warning exists:
    OpenTelemetry providers are process-global in this implementation, so the
    first configured `service.name` effectively wins for later shared runtimes.
    """
    global _ACTIVE_SERVICE_NAME
    if _ACTIVE_SERVICE_NAME is None:
        _ACTIVE_SERVICE_NAME = service_name
        return
    if _ACTIVE_SERVICE_NAME != service_name:
        LOGGER.warning(
            "observability already configured for service.name=%s; reusing existing process-level providers for service.name=%s",
            _ACTIVE_SERVICE_NAME,
            service_name,
        )


def _insecure_for_endpoint(endpoint: str) -> bool:
    """Return whether the OTLP exporter should use insecure gRPC transport."""
    return endpoint.lower().startswith("http://")


def _load_opentelemetry_modules() -> dict[str, Any]:
    """Load OpenTelemetry dependencies lazily for optional runtime support.

    Why this helper exists:
    several repo components can run without OTLP export enabled, so importing
    heavy optional dependencies only when needed keeps startup behavior aligned
    with those deployment modes.
    """
    try:
        from opentelemetry import metrics, trace
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional install set.
        raise RuntimeError(
            "OpenTelemetry dependencies are required when 'otlp-endpoints' is configured"
        ) from exc
    return {
        "metrics": metrics,
        "trace": trace,
        "set_logger_provider": set_logger_provider,
        "OTLPLogExporter": OTLPLogExporter,
        "OTLPMetricExporter": OTLPMetricExporter,
        "OTLPSpanExporter": OTLPSpanExporter,
        "OpenTelemetryMiddleware": OpenTelemetryMiddleware,
        "LoggingInstrumentor": LoggingInstrumentor,
        "LoggerProvider": LoggerProvider,
        "LoggingHandler": LoggingHandler,
        "BatchLogRecordProcessor": BatchLogRecordProcessor,
        "MeterProvider": MeterProvider,
        "PeriodicExportingMetricReader": PeriodicExportingMetricReader,
        "Resource": Resource,
        "TracerProvider": TracerProvider,
        "BatchSpanProcessor": BatchSpanProcessor,
    }


def configure_process_observability(
    *,
    service_name: str,
    config: ObservabilityConfig,
    log_level: int = logging.INFO,
) -> ObservabilityConfig:
    """Configure process-global OTLP exporters for logs, metrics, and traces.

    Why this helper exists:
    Quart apps and non-Quart runtimes both need the same process-level provider
    setup, while only some runtimes need app-level middleware registration.
    """
    global _LOGGING_ENABLED
    global _METRICS_ENABLED
    global _TRACING_ENABLED

    if config.enabled() is not True:
        return config

    _warn_if_service_name_changes(service_name)
    modules = _load_opentelemetry_modules()
    resource = modules["Resource"].create(
        {
            "service.name": service_name,
            "telemetry.sdk.language": "python",
        }
    )

    logs_endpoint = config.resolved_logs_endpoint
    if logs_endpoint and _LOGGING_ENABLED is not True:
        logger_provider = modules["LoggerProvider"](resource=resource)
        logger_provider.add_log_record_processor(
            modules["BatchLogRecordProcessor"](
                modules["OTLPLogExporter"](
                    endpoint=logs_endpoint,
                    insecure=_insecure_for_endpoint(logs_endpoint),
                )
            )
        )
        modules["set_logger_provider"](logger_provider)
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(
            modules["LoggingHandler"](
                level=log_level,
                logger_provider=logger_provider,
            )
        )
        modules["LoggingInstrumentor"]().instrument(set_logging_format=False)
        _LOGGING_ENABLED = True
        LOGGER.info("enabled OTLP log export endpoint=%s", logs_endpoint)

    traces_endpoint = config.resolved_traces_endpoint
    if traces_endpoint and _TRACING_ENABLED is not True:
        tracer_provider = modules["TracerProvider"](resource=resource)
        tracer_provider.add_span_processor(
            modules["BatchSpanProcessor"](
                modules["OTLPSpanExporter"](
                    endpoint=traces_endpoint,
                    insecure=_insecure_for_endpoint(traces_endpoint),
                )
            )
        )
        modules["trace"].set_tracer_provider(tracer_provider)
        _TRACING_ENABLED = True
        LOGGER.info("enabled OTLP trace export endpoint=%s", traces_endpoint)

    metrics_endpoint = config.resolved_metrics_endpoint
    if metrics_endpoint and _METRICS_ENABLED is not True:
        metric_reader = modules["PeriodicExportingMetricReader"](
            modules["OTLPMetricExporter"](
                endpoint=metrics_endpoint,
                insecure=_insecure_for_endpoint(metrics_endpoint),
            ),
            export_interval_millis=config.export_interval_seconds * 1000,
        )
        meter_provider = modules["MeterProvider"](
            resource=resource,
            metric_readers=[metric_reader],
        )
        modules["metrics"].set_meter_provider(meter_provider)
        _METRICS_ENABLED = True
        LOGGER.info(
            "enabled OTLP metric export endpoint=%s export_interval_seconds=%s",
            metrics_endpoint,
            config.export_interval_seconds,
        )

    return config


def attach_observability(
    app: Quart,
    *,
    service_name: str,
    config: ObservabilityConfig,
    log_level: int = logging.INFO,
) -> Quart:
    """Attach process-level OTLP setup plus Quart-specific middleware/hooks.

    Why this helper exists:
    Quart-based runtimes need the shared process-level exporters and, when
    enabled, request tracing and a simple request counter on the app itself.
    """
    if config.enabled() is not True:
        return app

    configure_process_observability(
        service_name=service_name,
        config=config,
        log_level=log_level,
    )
    modules = _load_opentelemetry_modules()

    if (
        config.resolved_traces_endpoint
        and app.extensions.get(APP_EXTENSION_ASGI_MIDDLEWARE_ENABLED) is not True
    ):
        app.asgi_app = modules["OpenTelemetryMiddleware"](app.asgi_app)
        app.extensions[APP_EXTENSION_ASGI_MIDDLEWARE_ENABLED] = True

    if (
        config.resolved_metrics_endpoint
        and app.extensions.get(APP_EXTENSION_REQUEST_COUNTER_ENABLED) is not True
    ):
        meter = modules["metrics"].get_meter(service_name)
        request_counter = meter.create_counter(
            name="app.requests",
            description="Application-level request counter",
            unit="1",
        )

        @app.before_request
        async def count_request() -> None:
            """Increment one simple request counter before each Quart request."""
            request_counter.add(1)

        app.extensions[APP_EXTENSION_REQUEST_COUNTER_ENABLED] = True

    app.extensions[APP_EXTENSION_OBSERVABILITY_ENABLED] = True
    return app
