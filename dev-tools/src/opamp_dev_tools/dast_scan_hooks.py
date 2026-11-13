# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Packaged-scan hooks that suppress reviewed OWASP ZAP false positives."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin, urlparse

BIG_REDIRECT_RULE_ID = "10044"
HTMLPREVIEW_REDIRECT_MARKER = "https://htmlpreview.github.io"
ALERT_ID_KEY = "id"
ALERT_OTHER_INFO_KEY = "other"
ALERT_OTHER_INFO_CAMEL_KEY = "otherInfo"
ALERT_OTHER_INFO_LOWER_KEY = "otherinfo"
ALERT_OTHER_INFO_KEYS = (
    ALERT_OTHER_INFO_KEY,
    ALERT_OTHER_INFO_CAMEL_KEY,
    ALERT_OTHER_INFO_LOWER_KEY,
)
HOOK_STATE_ZAP_CONNECTION_FIELD = "zap_connection"
MANAGED_TARGET_HOSTNAME = "opamp-dast-target"
MANAGED_TARGET_SEED_PATHS = (
    "/ui",
    "/config-service/ui",
    "/catalog",
    "/catalog/help",
    "/client-config-generator-service/ui",
    "/svr-credentials-manager-service/ui",
)
LOGGER = logging.getLogger(__name__)

_HOOK_STATE: dict[str, Any | None] = {HOOK_STATE_ZAP_CONNECTION_FIELD: None}


def zap_started(zap_client: Any, target: str) -> None:
    """Retain the ZAP client and seed every managed full-app browser surface.

    The packaged scan invokes this hook after ZAP starts and before crawling. Retaining the
    client allows the later alert hook to remove reviewed false positives from both packaged
    scan counts and the HTML, JSON, XML, and Markdown reports generated from the ZAP session.
    Managed scans also access each installed plugin UI explicitly because the provider menu is
    populated through JavaScript and is not fully discoverable by the traditional spider.

    Parameters:
        zap_client: ZAP Python API client created by the packaged scan.
        target: Scan target used to recognize and seed the managed full-app deployment.

    Returns:
        ``None``; the ZAP client is stored and managed application routes are added to its tree.
    """
    _HOOK_STATE[HOOK_STATE_ZAP_CONNECTION_FIELD] = zap_client
    if urlparse(target).hostname != MANAGED_TARGET_HOSTNAME:
        return
    for seed_path in MANAGED_TARGET_SEED_PATHS:
        seed_url = urljoin(target, seed_path)
        try:
            zap_client.urlopen(seed_url)
        except Exception as error:  # pylint: disable=broad-exception-caught
            LOGGER.warning("Unable to seed managed DAST route url=%s error=%s", seed_url, error)


def _alert_other_info(alert: dict[str, Any]) -> str:
    """Return an alert's version-compatible ZAP ``Other Info`` text.

    Parameters:
        alert: Alert mapping returned by the ZAP API.

    Returns:
        String form of the first supported ``Other Info`` field, or an empty string.
    """
    for key in ALERT_OTHER_INFO_KEYS:
        value = alert.get(key)
        if value is not None:
            return str(value)
    return ""


def _is_htmlpreview_big_redirect(alert: dict[str, Any]) -> bool:
    """Identify rule 10044 alerts caused by the reviewed external documentation redirect.

    Parameters:
        alert: Rule 10044 alert mapping returned by the ZAP API.

    Returns:
        ``True`` only when the alert details identify ``htmlpreview.github.io`` as the redirect
        destination.
    """
    return HTMLPREVIEW_REDIRECT_MARKER in _alert_other_info(alert)


def zap_get_alerts_wrap(alert_dict: dict[str, list[dict[str, Any]]]) -> None:
    """Remove reviewed htmlpreview rule 10044 alerts before reporting and exit evaluation.

    The packaged scan passes alerts grouped by rule identifier. Matching alerts are removed
    from that mapping and from the live ZAP session so they do not affect counts or retained
    reports. All other redirects and all other alert rules remain unchanged.

    Parameters:
        alert_dict: Mutable packaged-scan alert mapping grouped by ZAP rule identifier.

    Returns:
        ``None``; the supplied mapping and live ZAP session are updated in place.
    """
    rule_alerts = alert_dict.get(BIG_REDIRECT_RULE_ID)
    if not rule_alerts:
        return

    retained_alerts: list[dict[str, Any]] = []
    for alert in rule_alerts:
        if not _is_htmlpreview_big_redirect(alert):
            retained_alerts.append(alert)
            continue
        alert_id = alert.get(ALERT_ID_KEY)
        zap_client = _HOOK_STATE[HOOK_STATE_ZAP_CONNECTION_FIELD]
        if zap_client is not None and alert_id is not None:
            zap_client.alert.delete_alert(alert_id)
        LOGGER.debug(
            "Ignoring reviewed ZAP rule %s alert for %s redirect alert_id=%s",
            BIG_REDIRECT_RULE_ID,
            HTMLPREVIEW_REDIRECT_MARKER,
            alert_id,
        )

    if retained_alerts:
        alert_dict[BIG_REDIRECT_RULE_ID] = retained_alerts
    else:
        alert_dict.pop(BIG_REDIRECT_RULE_ID, None)
