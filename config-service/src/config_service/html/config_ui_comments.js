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

  function create(deps) {
    // Encapsulates comment metadata behavior so the main UI can stay focused on
    // rendering and event flow.
    function ensureMetaBlock(target) {
      if (!target || typeof target !== "object" || Array.isArray(target)) {
        return null;
      }
      if (!target._meta || typeof target._meta !== "object" || Array.isArray(target._meta)) {
        target._meta = {};
      }
      return target._meta;
    }

    function ensureFieldCommentMap(target) {
      var meta = ensureMetaBlock(target);
      if (!meta) {
        return null;
      }
      if (!meta.field_comment_lines || typeof meta.field_comment_lines !== "object" || Array.isArray(meta.field_comment_lines)) {
        meta.field_comment_lines = {};
      }
      return meta.field_comment_lines;
    }

    function commentLinesToText(lines) {
      if (!Array.isArray(lines)) {
        return "";
      }
      return lines
        .filter(function (line) {
          return typeof line === "string";
        })
        .join("\n")
        .trim();
    }

    function textToCommentLines(value) {
      var text = String(value || "").replace(/\r\n/g, "\n");
      var parts = text.split("\n");
      while (parts.length > 0 && parts[0].trim() === "") {
        parts.shift();
      }
      while (parts.length > 0 && parts[parts.length - 1].trim() === "") {
        parts.pop();
      }
      return parts.map(function (line) {
        return line.trimEnd();
      });
    }

    function objectCommentText(target) {
      var meta = ensureMetaBlock(target);
      if (!meta) {
        return "";
      }
      return commentLinesToText(meta.comment_lines);
    }

    function setObjectCommentText(target, value) {
      var meta = ensureMetaBlock(target);
      if (!meta) {
        return;
      }
      var lines = textToCommentLines(value);
      if (lines.length === 0) {
        delete meta.comment_lines;
        if (!meta.field_comment_lines || Object.keys(meta.field_comment_lines).length === 0) {
          delete target._meta;
        }
      } else {
        meta.comment_lines = lines;
      }
      deps.saveDoc();
    }

    function fieldCommentText(target, fieldName) {
      var meta = ensureMetaBlock(target);
      if (!meta || !meta.field_comment_lines) {
        return "";
      }
      return commentLinesToText(meta.field_comment_lines[fieldName]);
    }

    function setFieldCommentText(target, fieldName, value) {
      var fieldMap = ensureFieldCommentMap(target);
      if (!fieldMap) {
        return;
      }
      var lines = textToCommentLines(value);
      if (lines.length === 0) {
        delete fieldMap[fieldName];
        if (Object.keys(fieldMap).length === 0) {
          delete target._meta.field_comment_lines;
        }
        if (target._meta && !target._meta.comment_lines && !target._meta.field_comment_lines) {
          delete target._meta;
        }
      } else {
        fieldMap[fieldName] = lines;
      }
      deps.saveDoc();
    }

    function renameFieldComment(target, oldFieldName, newFieldName) {
      var meta = ensureMetaBlock(target);
      if (!meta || !meta.field_comment_lines || oldFieldName === newFieldName) {
        return;
      }
      if (Object.prototype.hasOwnProperty.call(meta.field_comment_lines, oldFieldName)) {
        meta.field_comment_lines[newFieldName] = meta.field_comment_lines[oldFieldName];
        delete meta.field_comment_lines[oldFieldName];
      }
    }

    function clearFieldComment(target, fieldName) {
      var meta = ensureMetaBlock(target);
      if (!meta || !meta.field_comment_lines) {
        return;
      }
      delete meta.field_comment_lines[fieldName];
      if (Object.keys(meta.field_comment_lines).length === 0) {
        delete meta.field_comment_lines;
      }
      if (!meta.comment_lines && !meta.field_comment_lines) {
        delete target._meta;
      }
    }

    function tokenizeLegacyCommentPath(path) {
      if (typeof path !== "string" || path.charAt(0) !== "$") {
        return null;
      }
      var tokens = [];
      var cursor = 1;
      while (cursor < path.length) {
        var char = path.charAt(cursor);
        if (char === ".") {
          cursor += 1;
          var nextDot = path.indexOf(".", cursor);
          var nextBracket = path.indexOf("[", cursor);
          var end = path.length;
          if (nextDot !== -1) {
            end = Math.min(end, nextDot);
          }
          if (nextBracket !== -1) {
            end = Math.min(end, nextBracket);
          }
          tokens.push(path.slice(cursor, end));
          cursor = end;
          continue;
        }
        if (char === "[") {
          var close = path.indexOf("]", cursor);
          if (close === -1) {
            return null;
          }
          tokens.push(Number(path.slice(cursor + 1, close)));
          cursor = close + 1;
          continue;
        }
        return null;
      }
      return tokens;
    }

    function migrateLegacyAnnotationsToMeta() {
      // One-way migration for older `annotations` shape into `_meta` blocks.
      if (!deps.state.doc || !deps.state.doc.annotations || Object.keys(deps.state.doc.annotations).length === 0) {
        return;
      }
      var annotations = deps.state.doc.annotations;
      Object.keys(annotations).forEach(function (path) {
        var tokens = tokenizeLegacyCommentPath(path);
        if (!tokens || tokens.length === 0) {
          return;
        }
        var cursor = deps.state.doc.config;
        var parent = null;
        var lastToken = null;
        for (var index = 0; index < tokens.length; index += 1) {
          lastToken = tokens[index];
          parent = cursor;
          if (parent === undefined || parent === null) {
            return;
          }
          cursor = parent[lastToken];
        }
        var text = String(annotations[path] || "");
        if (cursor && typeof cursor === "object" && !Array.isArray(cursor)) {
          setObjectCommentText(cursor, text);
          return;
        }
        if (parent && typeof parent === "object" && typeof lastToken === "string") {
          setFieldCommentText(parent, lastToken, text);
        }
      });
      deps.state.doc.annotations = {};
    }

    function hasCommentText(target, fieldName) {
      var text = fieldName ? fieldCommentText(target, fieldName) : objectCommentText(target);
      return Boolean(String(text || "").trim());
    }

    function isCommentEditorOpen(toggleKey, target, fieldName) {
      if (toggleKey && Object.prototype.hasOwnProperty.call(deps.state.commentOpen, toggleKey)) {
        return Boolean(deps.state.commentOpen[toggleKey]);
      }
      return hasCommentText(target, fieldName);
    }

    function setCommentEditorOpen(toggleKey, isOpen) {
      if (!toggleKey) {
        return;
      }
      deps.state.commentOpen[toggleKey] = Boolean(isOpen);
    }

    function createCommentToggleButton(toggleKey, target, fieldName, labelText) {
      // Compact toggle button used across cards for optional comment editors.
      var btn = document.createElement("button");
      var isOpen = isCommentEditorOpen(toggleKey, target, fieldName);
      var hasContent = hasCommentText(target, fieldName);
      btn.type = "button";
      btn.textContent = hasContent ? "📝" : "🗒";
      btn.className = "icon-button icon-note";
      if (isOpen) {
        btn.classList.add("is-active");
      }
      if (hasContent) {
        btn.classList.add("has-comment");
      }
      btn.title = (isOpen ? "Hide " : "Open ") + (labelText || "comment editor");
      btn.setAttribute("aria-label", (isOpen ? "Hide " : "Open ") + (labelText || "comment editor"));
      btn.addEventListener("click", function () {
        setCommentEditorOpen(toggleKey, !isOpen);
        deps.renderAll();
      });
      return btn;
    }

    function createCommentEditorPanel(target, labelText, fieldName, toggleKey) {
      var wrap = document.createElement("div");
      wrap.className = "comment-editor";
      if (!isCommentEditorOpen(toggleKey, target, fieldName)) {
        wrap.classList.add("hidden");
      }

      var label = document.createElement("label");
      label.className = "comment-label";
      label.textContent = labelText || "Comment";

      var input = document.createElement("textarea");
      input.className = "comment-input";
      input.rows = 2;
      input.placeholder = "Optional comment";
      input.value = fieldName ? fieldCommentText(target, fieldName) : objectCommentText(target);
      input.disabled = deps.isReadOnlyMode();
      input.addEventListener("change", function () {
        if (fieldName) {
          setFieldCommentText(target, fieldName, input.value);
          setCommentEditorOpen(toggleKey, true);
          deps.saveDoc();
          return;
        }
        setObjectCommentText(target, input.value);
        setCommentEditorOpen(toggleKey, true);
        deps.saveDoc();
      });

      label.appendChild(input);
      wrap.appendChild(label);
      return wrap;
    }

    function createCommentEditor(target, labelText, fieldName) {
      return createCommentEditorPanel(target, labelText, fieldName, "");
    }

    return {
      ensureMetaBlock: ensureMetaBlock,
      ensureFieldCommentMap: ensureFieldCommentMap,
      commentLinesToText: commentLinesToText,
      textToCommentLines: textToCommentLines,
      objectCommentText: objectCommentText,
      setObjectCommentText: setObjectCommentText,
      fieldCommentText: fieldCommentText,
      setFieldCommentText: setFieldCommentText,
      renameFieldComment: renameFieldComment,
      clearFieldComment: clearFieldComment,
      tokenizeLegacyCommentPath: tokenizeLegacyCommentPath,
      migrateLegacyAnnotationsToMeta: migrateLegacyAnnotationsToMeta,
      createCommentEditor: createCommentEditor,
      hasCommentText: hasCommentText,
      isCommentEditorOpen: isCommentEditorOpen,
      setCommentEditorOpen: setCommentEditorOpen,
      createCommentToggleButton: createCommentToggleButton,
      createCommentEditorPanel: createCommentEditorPanel,
    };
  }

  global.ConfigServiceUiComments = {
    create: create,
  };
})(window);
