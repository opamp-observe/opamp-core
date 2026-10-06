/*
 * Copyright 2026 mp3monster.org
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

(function bindClientConfigGenerator(globalObject) {
  "use strict";

  /** Wire static controls to the injected behavior API and start the UI. */
  function initializeBindings() {
    const context = globalObject.ClientConfigGeneratorFramework.create();
    const functions = context.functions;
    globalObject.ClientConfigGenerator = context;
    globalObject.document.getElementById("browseConfigurationButton").addEventListener("click", functions.browseConfigurationFiles);
    globalObject.document.getElementById("newConfigurationButton").addEventListener("click", functions.startNewConfiguration);
    globalObject.document.getElementById("loadButton").addEventListener("click", functions.loadSelectedConfiguration);
    globalObject.document.getElementById("configurationSelect").addEventListener("change", function selectConfiguration(event) {
      functions.selectConfigurationName(event.target.value);
    });
    globalObject.document.getElementById("validateButton").addEventListener("click", functions.validateConfiguration);
    globalObject.document.getElementById("saveButton").addEventListener("click", functions.saveConfiguration);
    globalObject.document.getElementById("processMode").addEventListener("change", function changeMode(event) {
      functions.setMode(event.target.value);
    });
    functions.initialize();
  }

  globalObject.addEventListener("DOMContentLoaded", initializeBindings);
})(window);
