# Copyright 2026 opamp.info
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

"""Classifier coverage for catalog-service config file detection."""

from __future__ import annotations

import io
import logging

from catalog_service.config_classifiers import (
    CompositeConfigClassifier,
    FluentBitClassicConfigClassifier,
    FluentBitYamlConfigClassifier,
    FluentdConfigClassifier,
    JsonConfigClassifier,
)


def test_fluentbit_classic_classifier_extracts_header_attributes() -> None:
    classifier = FluentBitClassicConfigClassifier()
    file_handle = io.StringIO(
        "\n".join(
            [
                "# config-service: config_type=fluentbit",
                "# config-service: version=5.0.4",
                "# config-service: config_version=release-27",
                "[SERVICE]",
                "  Flush 1",
            ]
        )
    )

    result = classifier.classify(file_handle)

    assert result is not None
    assert result.config_type == "fluentbit"
    assert result.attributes == {
        "version": "5.0.4",
        "config_version": "release-27",
    }


def test_fluentbit_yaml_classifier_recognizes_yaml_structure() -> None:
    classifier = FluentBitYamlConfigClassifier()
    file_handle = io.StringIO(
        "\n".join(
            [
                "# config-service: config_type=fluentbit",
                "# config-service: profile=prod",
                "service:",
                "  flush: 1",
                "pipeline:",
                "  inputs: []",
                "  filters: []",
                "  outputs: []",
            ]
        )
    )

    result = classifier.classify(file_handle)

    assert result is not None
    assert result.config_type == "fluentbit"
    assert result.attributes == {"profile": "prod"}


def test_fluentd_classifier_recognizes_directive_syntax() -> None:
    classifier = FluentdConfigClassifier()
    file_handle = io.StringIO(
        "\n".join(
            [
                "# config-service: config_type=fluentd",
                "# config-service: version=1.16",
                "<source>",
                "  @type forward",
                "</source>",
            ]
        )
    )

    result = classifier.classify(file_handle)

    assert result is not None
    assert result.config_type == "fluentd"
    assert result.attributes == {"version": "1.16"}


def test_composite_classifier_returns_none_for_unrecognized_content() -> None:
    classifier = CompositeConfigClassifier()
    file_handle = io.StringIO("this is not a supported config format")

    result = classifier.classify(file_handle)

    assert result is None


def test_composite_classifier_uses_first_matching_classifier() -> None:
    classifier = CompositeConfigClassifier()
    file_handle = io.StringIO(
        "\n".join(
            [
                "; config-service: config_type=fluentd",
                "; config-service: owner=team-observability",
                "<match **>",
                "  @type null",
                "</match>",
            ]
        )
    )

    result = classifier.classify(file_handle)

    assert result is not None
    assert result.config_type == "fluentd"
    assert result.attributes == {"owner": "team-observability"}


def test_classifier_logs_identified_properties_at_debug(caplog) -> None:
    classifier = FluentBitClassicConfigClassifier()
    with caplog.at_level(logging.DEBUG):
        result = classifier.classify(
            io.StringIO(
                "\n".join(
                    [
                        "# config-service: config_type=fluentbit",
                        "# config-service: version=5.0.4",
                        "[SERVICE]",
                        "  Flush 1",
                    ]
                )
            )
        )

    assert result is not None
    assert any(
        (
            record.levelno == logging.DEBUG
            and "classified config properties" in record.getMessage()
            and "FluentBitClassicConfigClassifier" in record.getMessage()
            and "version" in record.getMessage()
            and "5.0.4" in record.getMessage()
        )
        for record in caplog.records
    )


def test_json_classifier_recognizes_engine_and_version() -> None:
    classifier = JsonConfigClassifier()
    file_handle = io.StringIO(
        "\n".join(
            [
                "{",
                '  "engine": "fluentbit",',
                '  "version": "5.0.4"',
                "}",
            ]
        )
    )

    result = classifier.classify(file_handle)

    assert result is not None
    assert result.config_type == "fluentbit"
    assert result.attributes == {
        "engine": "fluentbit",
        "version": "5.0.4",
    }
