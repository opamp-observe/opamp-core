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

(function exposeClientConfigGeneratorFramework(globalObject) {
  "use strict";

  /** Build the UI context from namespace factories without implicit dependencies. */
  function create() {
    const state = globalObject.ClientConfigGeneratorState.create();
    const functions = globalObject.ClientConfigGeneratorFunctions.create({
      documentObject: globalObject.document,
      fetchFunction: globalObject.fetch.bind(globalObject),
      state,
    });
    return { functions, state };
  }

  globalObject.ClientConfigGeneratorFramework = { create };
})(window);
