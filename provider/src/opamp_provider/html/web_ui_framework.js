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

(function (global) {
  "use strict";

  function requireFactory(namespaceName, methodName) {
    var namespace = global[namespaceName];
    if (!namespace || typeof namespace[methodName] !== "function") {
      throw new Error(
        namespaceName + "." + methodName + " is required to bootstrap provider UI"
      );
    }
    return namespace[methodName];
  }

  function createRuntime() {
    var stateFactory = requireFactory("ProviderUiState", "create");
    var runtime = stateFactory();
    var functionsFactory = requireFactory("ProviderUiFunctions", "create");
    runtime.actions = functionsFactory(runtime);
    return runtime;
  }

  function bootstrap() {
    var runtime = createRuntime();
    var bindingsFactory = requireFactory("ProviderUiBindings", "create");
    var bindings = bindingsFactory(runtime);
    if (!bindings || typeof bindings.bind !== "function") {
      throw new Error("ProviderUiBindings.create(...) must return { bind() }");
    }
    bindings.bind();
    return runtime;
  }

  global.ProviderUiFramework = {
    createRuntime: createRuntime,
    bootstrap: bootstrap,
  };
})(window);
