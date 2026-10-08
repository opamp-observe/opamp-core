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

(function () {
  "use strict";

  const MERMAID_CODE_SELECTOR = "pre > code.language-mermaid";
  const MERMAID_CONTAINER_CLASS = "mermaid";
  const MERMAID_SECURITY_LEVEL = "strict";
  const MERMAID_START_ON_LOAD = false;
  const MERMAID_THEME = "default";

  /**
   * Replaces a rendered fenced Mermaid code block with a Mermaid container.
   *
   * @param {HTMLElement} codeBlock Rendered Markdown code element containing Mermaid source.
   * @returns {void}
   */
  function replaceCodeBlockWithMermaidContainer(codeBlock) {
    const preformattedBlock = codeBlock.parentElement;
    const mermaidContainer = document.createElement("div");

    mermaidContainer.className = MERMAID_CONTAINER_CLASS;
    mermaidContainer.textContent = codeBlock.textContent;

    preformattedBlock.replaceWith(mermaidContainer);
  }

  /**
   * Converts all fenced Mermaid code blocks on the page into renderable containers.
   *
   * @returns {void}
   */
  function prepareMermaidContainers() {
    const codeBlocks = document.querySelectorAll(MERMAID_CODE_SELECTOR);

    codeBlocks.forEach(replaceCodeBlockWithMermaidContainer);
  }

  /**
   * Initializes Mermaid after the CDN script and document body are available.
   *
   * @returns {void}
   */
  function renderMermaidDiagrams() {
    if (!window.mermaid) {
      return;
    }

    prepareMermaidContainers();
    window.mermaid.initialize({
      securityLevel: MERMAID_SECURITY_LEVEL,
      startOnLoad: MERMAID_START_ON_LOAD,
      theme: MERMAID_THEME,
    });
    const renderPromise = window.mermaid.run();

    if (renderPromise && typeof renderPromise.catch === "function") {
      renderPromise.catch(function (renderError) {
        console.warn("Unable to render one or more Mermaid diagrams.", renderError);
      });
    }
  }

  window.addEventListener("DOMContentLoaded", renderMermaidDiagrams);
})();
