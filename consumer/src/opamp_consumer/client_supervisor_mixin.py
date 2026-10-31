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

"""Supervisor lifecycle implementation for managed agent subprocesses."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time

from opamp_consumer.client_runtime_mixin import _BaseClientProcessLifecycle
from opamp_consumer.exceptions import AgentException


class ClientSupervisorMixin(_BaseClientProcessLifecycle):
    """Lifecycle implementation that launches and manages a subprocess directly."""

    _runtime_agent_command = "agent"
    _runtime_config_flag = "-c"

    def _resolve_launch_command(self, raw_command: list[str]) -> list[str]:
        """Resolve the runtime executable from PATH and normalize Windows wrappers."""
        executable = str(raw_command[0] if raw_command else "").strip()
        if not executable:
            raise FileNotFoundError("agent runtime command is empty")

        resolved_executable = shutil.which(executable)
        if not resolved_executable:
            raise FileNotFoundError(executable)

        command = [resolved_executable, *raw_command[1:]]
        if os.name == "nt" and resolved_executable.lower().endswith((".bat", ".cmd")):
            return ["cmd", "/c", resolved_executable, *raw_command[1:]]
        return command

    def launch_agent_process(self) -> bool:
        """Launch the configured agent process using runtime command metadata."""
        logger = logging.getLogger(__name__)
        try:
            hot_deploy_flag = str(self._owner.check_hot_deploy() or "").strip()
        except Exception:
            logger.exception(
                "failed to resolve hot deploy flag for command=%s",
                self._owner._runtime_agent_command,
            )
            hot_deploy_flag = ""
        raw_command = [
            self._owner._runtime_agent_command,
            *(self._owner.config.agent_additional_params or []),
            *([hot_deploy_flag] if hot_deploy_flag else []),
            self._owner._runtime_config_flag,
            self._owner.config.agent_config_path,
        ]
        logger.debug(
            "About to start agent process with config %s and command %s",
            self._owner.config.agent_config_path,
            raw_command,
        )
        command = raw_command
        try:
            command = self._resolve_launch_command(raw_command)
            logger.debug("Resolved runtime command: %s", command)
            with self._owner.data.process_lock:
                process_response: subprocess.Popen[bytes] = subprocess.Popen(command)
                self._owner.data.agent_process = process_response
                self._owner.data.observed_process_pid = None
                self._owner.data.launched_at = time.time_ns()
        except FileNotFoundError as file_error:
            logger.error(
                "Agent launch failed because command was not found (%s): %s",
                self._owner._runtime_agent_command,
                file_error,
            )
            return False
        except Exception as launch_error:  # pragma: no cover - env-dependent
            logger.exception("Agent launch failed for command %s", command)
            logger.debug("Agent launch exception detail: %s", launch_error)
            return False
        logger.info("Launch result = %s", process_response)
        return True

    def terminate_agent_process(self) -> None:
        """Terminate the launched Agent process if available."""
        logger = logging.getLogger(__name__)
        with self._owner.data.process_lock:
            process = self._owner.data.agent_process
            self._owner.data.allow_heartbeat = False
            if process is None:
                return
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Agent did not terminate in time; killing process")
                print("Agent did not terminate in time; killing process")
                process.kill()
                process.wait(timeout=5)
            self._owner.data.agent_process = None

    def restart_agent_process(self) -> bool:
        """Stop the current agent process and start a new instance."""
        logger = logging.getLogger(__name__)
        logger.info("Restarting agent process")
        lock_acquired = self._owner.data.process_lock.acquire(timeout=30)
        if not lock_acquired:
            raise AgentException(
                "Timed out waiting for process lock while restarting agent process"
            )
        try:
            self._owner.terminate_agent_process()
            relaunched = self._owner.launch_agent_process()
        finally:
            self._owner.data.process_lock.release()
        if not relaunched:
            raise AgentException("Failed to restart agent process")
        logger.info("Agent process restarted")
        return relaunched
