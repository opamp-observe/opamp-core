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

"""Observer lifecycle implementation for externally managed agent processes."""

from __future__ import annotations

import logging
import time

from opamp_consumer.client_runtime_mixin import _BaseClientProcessLifecycle
from opamp_consumer.exceptions import AgentException
from opamp_consumer.process_utils import ProcessUtils


class ClientObserverMixin(_BaseClientProcessLifecycle):
    """Lifecycle implementation that observes an externally managed process."""

    _restart_wait_after_signal_seconds = 3.0
    _restart_wait_before_relaunch_seconds = 1.0

    def _resolve_pid(self) -> int | None:
        """Resolve pid from cached value or regex process discovery."""
        cached_pid = self._owner.data.observed_process_pid
        if cached_pid and ProcessUtils.is_process_running(cached_pid):
            return cached_pid

        regex = str(self._owner.config.process_detection_regex or "").strip()
        if not regex:
            return None
        pid = ProcessUtils.find_pid_by_regex(regex)
        self._owner.data.observed_process_pid = pid
        return pid

    def launch_agent_process(self) -> bool:
        """Locate an external process by regex and mark launch success when found."""
        logger = logging.getLogger(__name__)
        regex = str(self._owner.config.process_detection_regex or "").strip()
        if not regex:
            logger.error(
                "observer mode requires process_detection_regex to locate a running process"
            )
            return False

        pid = ProcessUtils.find_pid_by_regex(regex)
        if pid is None:
            logger.warning(
                "observer mode failed to locate process for regex: %s",
                regex,
            )
            return False

        self._owner.data.observed_process_pid = pid
        self._owner.data.agent_process = None
        self._owner.data.launched_at = time.time_ns()
        logger.info("observer mode attached to process pid=%s", pid)
        return True

    def terminate_agent_process(self) -> None:
        """Terminate observed process with graceful signal fallback to force kill."""
        logger = logging.getLogger(__name__)
        self._owner.data.allow_heartbeat = False
        pid = self._resolve_pid()
        if pid is None:
            logger.info("observer mode terminate skipped; no matching process found")
            return

        if ProcessUtils.can_send_signal():
            sent = ProcessUtils.send_termination_signal(pid)
            if sent:
                time.sleep(self._restart_wait_after_signal_seconds)

        if ProcessUtils.is_process_running(pid):
            logger.warning(
                "observer mode process still alive after signal, forcing terminate pid=%s",
                pid,
            )
            ProcessUtils.terminate_process(pid)

        if ProcessUtils.is_process_running(pid):
            logger.warning(
                "observer mode process still alive after terminate(), forcing kill pid=%s",
                pid,
            )
            ProcessUtils.kill_process(pid)

        if not ProcessUtils.is_process_running(pid):
            self._owner.data.observed_process_pid = None

    def restart_agent_process(self) -> bool:
        """Restart observed process using terminate+re-discover workflow."""
        logger = logging.getLogger(__name__)
        logger.info("Restarting observed agent process")
        lock_acquired = self._owner.data.process_lock.acquire(timeout=30)
        if not lock_acquired:
            raise AgentException(
                "Timed out waiting for process lock while restarting observed process"
            )
        try:
            self._owner.terminate_agent_process()
            time.sleep(self._restart_wait_before_relaunch_seconds)
            relaunched = self._owner.launch_agent_process()
        finally:
            self._owner.data.process_lock.release()

        if not relaunched:
            raise AgentException("Failed to re-attach to observed process")
        logger.info("Observed process restart completed")
        return relaunched
