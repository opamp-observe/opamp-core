/*
 * Copyright 2026 opamp.info
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
const AUTH_TOKEN_STORAGE_KEY = "opamp_ui_bearer_token";

    function loadStoredAuthToken() {
      try {
        return String(window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) || "").trim();
      } catch (_error) {
        return "";
      }
    }

    async function apiFetch(resource, options = {}) {
      const token = loadStoredAuthToken();
      const headers = {
        ...(options.headers || {}),
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      return fetch(resource, {
        ...options,
        headers,
      });
    }

    async function loadCustomCommands() {
      const list = document.getElementById("customCommandList");
      try {
        const resp = await apiFetch("/api/commands/custom");
        if (!resp.ok) {
          if (resp.status === 401 || resp.status === 403) {
            list.innerHTML = "<li>Authorization required. Set a bearer token in Global Settings → Server Settings.</li>";
            return;
          }
          list.innerHTML = "<li>Failed to load custom commands.</li>";
          return;
        }
        const payload = await resp.json();
        const commands = Array.isArray(payload.commands) ? payload.commands : [];
        if (!commands.length) {
          list.innerHTML = "<li>No custom commands are currently registered.</li>";
          return;
        }
        list.innerHTML = "";
        commands
          .slice()
          .sort((a, b) => String(a.displayname || "").localeCompare(String(b.displayname || "")))
          .forEach(cmd => {
            const li = document.createElement("li");
            const displayName = cmd.displayname || cmd.operation || cmd.fqdn || "Unnamed Command";
            const description = cmd.description || "No description provided.";
            li.innerHTML = `<strong>${displayName}</strong><br>${description}`;
            list.appendChild(li);
          });
      } catch (err) {
        list.innerHTML = "<li>Failed to load custom commands.</li>";
      }
    }

    loadCustomCommands();
