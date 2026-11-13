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
(function() {
        const historyBackButton = document.querySelector('[data-history-back-button="true"]');
        if (historyBackButton) {
          historyBackButton.addEventListener('click', () => window.history.back());
        }
        function syncHistoryBackButton() {
          const button = document.querySelector('[data-history-back-button="true"]');
          if (!button) return;
          if (button.getAttribute('aria-hidden') === 'true') return;
          if (window.history.length > 1) {
            button.removeAttribute('hidden');
            return;
          }
          button.setAttribute('hidden', 'hidden');
        }

        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', syncHistoryBackButton, { once: true });
        } else {
          syncHistoryBackButton();
        }
        window.addEventListener('pageshow', syncHistoryBackButton);

        const CATALOG_UI_COLUMN_ORDER_STORAGE_KEY = 'catalog_ui_column_order';
        const DEFAULT_UI_REFRESH_SECONDS = 120;
        const CONFIGURED_UI_REFRESH_SECONDS = parseInt(__CATALOG_UI_REFRESH_SECONDS__, 10);
        const UI_REFRESH_SECONDS = Number.isNaN(CONFIGURED_UI_REFRESH_SECONDS) || CONFIGURED_UI_REFRESH_SECONDS <= 0
          ? DEFAULT_UI_REFRESH_SECONDS
          : CONFIGURED_UI_REFRESH_SECONDS;
        const CATALOG_SELECTION_CALLBACK_QUERY = 'selection_callback';
        const CATALOG_SELECTION_APPLIED_MESSAGE_TYPE = 'opamp-catalog-selection-applied';
        const SELECTION_COLUMN_KEY = 'selected';
        const SELECTION_FILTER_BOTH = 'both';
        const SELECTION_FILTER_SELECTED = 'selected';
        const SELECTION_FILTER_UNSELECTED = 'unselected';
        const api = window.CatalogServiceUiApi.create({
          routePath: __CATALOG_ROUTE_PATH__,
          uiFeaturesPath: '/api/ui/features',
          clientErrorsEndpoint: __CATALOG_CLIENT_ERRORS_ENDPOINT__
        });
        const COLUMN_LABEL_OVERRIDES = {
          selected: 'selected',
          config_type: 'config type (metadata)',
          engine: 'engine (inferred)'
        };
        const state = {
          rows: [],
          columns: [],
          sortKey: 'folder',
          sortDir: 'asc',
          page: 1,
          pageSize: 20,
          filter: '',
          columnFilters: {},
          selectedPaths: [],
          selectionFilter: SELECTION_FILTER_BOTH,
          uiFeatureItems: [],
          configEditorUrl: '',
          configEditorAvailable: false
        };
        let draggingColumnKey = '';
        let skipSortClickForColumn = '';
        let isLoadingRows = false;
        let refreshTimer = null;
        const filterInput = document.getElementById('catalogFilter');
        const pageSizeInput = document.getElementById('catalogPageSize');
        const summary = document.getElementById('catalogSummary');
        const headerRow = document.getElementById('catalogHeaderRow');
        const columnFilterRow = document.getElementById('catalogColumnFilterRow');
        const body = document.getElementById('catalogBody');
        const pageNum = document.getElementById('catalogPageNum');
        const selectionActions = document.getElementById('catalogSelectionActions');
        const applySelectionButton = document.getElementById('catalogApplySelectionBtn');
        const applySelectionStatus = document.getElementById('catalogApplySelectionStatus');
        const featureMenuGroup = document.getElementById('featureMenuGroup');
        const featureMenuSelect = document.getElementById('featureMenuSelect');
        const readonlyOverlay = document.getElementById('catalogReadonlyOverlay');
        const readonlyTitle = document.getElementById('catalogReadonlyTitle');
        const readonlyPath = document.getElementById('catalogReadonlyPath');
        const readonlyText = document.getElementById('catalogReadonlyText');
        const readonlyError = document.getElementById('catalogReadonlyError');
        const selectionCallbackUrl = String(
          new URLSearchParams(window.location.search).get(CATALOG_SELECTION_CALLBACK_QUERY) || ''
        ).trim();

        function hasSelectionCallback() {
          return Boolean(selectionCallbackUrl);
        }

        function setApplySelectionStatus(message, tone) {
          if (!applySelectionStatus) return;
          applySelectionStatus.textContent = String(message || '');
          applySelectionStatus.classList.remove('success', 'error');
          if (tone === 'success' || tone === 'error') {
            applySelectionStatus.classList.add(tone);
          }
        }

        function selectedRowsInOrder() {
          const rowsByPath = new Map();
          state.rows.forEach(row => {
            const path = rowPath(row);
            if (!path) return;
            rowsByPath.set(path, row);
          });
          return state.selectedPaths
            .map(path => rowsByPath.get(path))
            .filter(row => Boolean(row));
        }

        function syncSelectionActions() {
          if (!selectionActions || !applySelectionButton) return;
          const callbackEnabled = hasSelectionCallback();
          selectionActions.classList.toggle('hidden', !callbackEnabled);
          applySelectionButton.classList.toggle('hidden', !callbackEnabled);
          applySelectionButton.disabled = !callbackEnabled || state.selectedPaths.length === 0;
          if (!callbackEnabled) {
            setApplySelectionStatus('');
            return;
          }
          if (state.selectedPaths.length === 0) {
            setApplySelectionStatus('Select one or more files, then Apply to return them to the server console.');
          }
        }

        async function applySelectedRows() {
          if (!hasSelectionCallback() || !applySelectionButton) return;
          const selectedRows = selectedRowsInOrder();
          if (selectedRows.length === 0) {
            setApplySelectionStatus('Select at least one file before applying.', 'error');
            return;
          }
          const originalLabel = applySelectionButton.textContent;
          applySelectionButton.disabled = true;
          applySelectionButton.textContent = 'Applying...';
          setApplySelectionStatus(`Applying ${selectedRows.length} selected file${selectedRows.length === 1 ? '' : 's'}...`);
          try {
            const payload = await api.postSelectionCallback(selectionCallbackUrl, {
              files: selectedRows.map(row => ({
                source_path: row.path,
              })),
            });
            if (window.opener && typeof window.opener.postMessage === 'function') {
              const targetOrigin = new URL(selectionCallbackUrl, window.location.origin).origin;
              window.opener.postMessage(
                {
                  type: CATALOG_SELECTION_APPLIED_MESSAGE_TYPE,
                  client_id: String(payload && payload.client_id ? payload.client_id : ''),
                  files: Array.isArray(payload && payload.files) ? payload.files : [],
                },
                targetOrigin
              );
            }
            setApplySelectionStatus(
              `Applied ${selectedRows.length} selected file${selectedRows.length === 1 ? '' : 's'}.`,
              'success'
            );
            window.close();
          } catch (err) {
            setApplySelectionStatus(
              String(err && err.message ? err.message : err || 'Failed to apply selected files.'),
              'error'
            );
          } finally {
            applySelectionButton.disabled = state.selectedPaths.length === 0;
            applySelectionButton.textContent = originalLabel;
          }
        }

        function normalizeColumns(columns) {
          if (!Array.isArray(columns)) return [];
          const deduped = [];
          columns.forEach(column => {
            const normalized = String(column || '').trim();
            if (!normalized || deduped.includes(normalized)) return;
            deduped.push(normalized);
          });
          return deduped;
        }

        function sanitizeColumnOrder(order, availableColumns) {
          const available = normalizeColumns(availableColumns);
          const requested = normalizeColumns(order);
          const selected = requested.filter(column => available.includes(column));
          const missing = available.filter(column => !selected.includes(column));
          return [...selected, ...missing];
        }

        function normalizeColumnFilters(filters, columns) {
          const normalized = {};
          normalizeColumns(columns).forEach(column => {
            normalized[column] = String(filters && filters[column] ? filters[column] : '');
          });
          return normalized;
        }

        // Return a stable row identifier so selection survives filtering and paging changes.
        function rowPath(row) {
          return String(row && row.path ? row.path : '').trim();
        }

        // Return whether one row is currently selected by checkbox state.
        function isRowSelected(row) {
          const path = rowPath(row);
          if (!path) return false;
          return state.selectedPaths.includes(path);
        }

        // Toggle row selection while preserving click order for future workflow extensions.
        function setRowSelected(row, selected) {
          const path = rowPath(row);
          if (!path) return;
          const nextSelected = Boolean(selected);
          const withoutPath = state.selectedPaths.filter(selectedPath => selectedPath !== path);
          state.selectedPaths = nextSelected ? [...withoutPath, path] : withoutPath;
        }

        // Keep selected paths aligned with the currently loaded catalog rows.
        function reconcileSelectedPaths(rows) {
          const availablePaths = new Set(
            (Array.isArray(rows) ? rows : [])
              .map(row => rowPath(row))
              .filter(path => Boolean(path))
          );
          state.selectedPaths = state.selectedPaths.filter(path => availablePaths.has(path));
        }

        // Return whether one row should remain visible for the active selection filter.
        function rowMatchesSelectionFilter(row) {
          if (state.selectionFilter === SELECTION_FILTER_SELECTED) {
            return isRowSelected(row);
          }
          if (state.selectionFilter === SELECTION_FILTER_UNSELECTED) {
            return !isRowSelected(row);
          }
          return true;
        }

        function readStoredColumnOrder(availableColumns) {
          const fallback = normalizeColumns(availableColumns);
          try {
            const raw = window.localStorage.getItem(CATALOG_UI_COLUMN_ORDER_STORAGE_KEY);
            if (!raw) return fallback;
            const parsed = JSON.parse(raw);
            return sanitizeColumnOrder(parsed, fallback);
          } catch (_err) {
            return fallback;
          }
        }

        function persistColumnOrder() {
          try {
            window.localStorage.setItem(
              CATALOG_UI_COLUMN_ORDER_STORAGE_KEY,
              JSON.stringify(state.columns)
            );
          } catch (_err) {
            // Ignore storage failures and keep the in-memory ordering.
          }
        }

        function moveColumnRelativeToTarget(dragKey, targetKey, placeAfter) {
          const normalizedDrag = String(dragKey || '').trim();
          const normalizedTarget = String(targetKey || '').trim();
          if (!normalizedDrag || !normalizedTarget || normalizedDrag === normalizedTarget) return false;
          const withoutDrag = state.columns.filter(column => column !== normalizedDrag);
          const targetIndex = withoutDrag.indexOf(normalizedTarget);
          if (targetIndex < 0) return false;
          const insertIndex = placeAfter ? targetIndex + 1 : targetIndex;
          withoutDrag.splice(insertIndex, 0, normalizedDrag);
          state.columns = sanitizeColumnOrder(withoutDrag, state.columns);
          return true;
        }

        function sortedFilteredRows() {
          const needle = String(state.filter || '').toLowerCase();
          const filtered = state.rows.filter(row => {
            if (!rowMatchesSelectionFilter(row)) return false;
            if (needle) {
              const values = state.columns.map(col => valueForColumnFilter(row, col));
              if (!values.join(' ').toLowerCase().includes(needle)) return false;
            }
            for (const col of state.columns) {
              const columnNeedle = String(state.columnFilters[col] || '').trim().toLowerCase();
              if (!columnNeedle) continue;
              const value = valueForColumnFilter(row, col).toLowerCase();
              if (!value.includes(columnNeedle)) return false;
            }
            return true;
          });
          const sorted = [...filtered].sort((a, b) => {
            const va = valueFor(a, state.sortKey);
            const vb = valueFor(b, state.sortKey);
            if (va > vb) return state.sortDir === 'asc' ? 1 : -1;
            if (va < vb) return state.sortDir === 'asc' ? -1 : 1;
            return 0;
          });
          return sorted;
        }

        function valueFor(row, key) {
          if (key === 'folder') return String(row.folder || '').toLowerCase();
          if (key === 'filename') return String(row.filename || '').toLowerCase();
          if (key === 'last_edited') return String(row.last_edited || '');
          return String((row.metadata && row.metadata[key]) || '').toLowerCase();
        }

        function rowValueForColumn(row, key, formatTimestamps) {
          if (key === 'folder') return String(row.folder || '');
          if (key === 'filename') return String(row.filename || '');
          if (key === 'last_edited') {
            if (formatTimestamps) return formatCatalogTimestamp(row.last_edited || '');
            return String(row.last_edited || '');
          }
          return String((row.metadata && row.metadata[key]) || '');
        }

        function valueForColumnFilter(row, key) {
          return rowValueForColumn(row, key, true);
        }

        function displayColumnName(columnName) {
          const normalizedColumnName = String(columnName || '');
          if (Object.prototype.hasOwnProperty.call(COLUMN_LABEL_OVERRIDES, normalizedColumnName)) {
            return COLUMN_LABEL_OVERRIDES[normalizedColumnName];
          }
          if (columnName === 'last_edited') return 'last edited';
          return normalizedColumnName;
        }

        function formatCatalogTimestamp(value) {
          const raw = String(value || '').trim();
          if (!raw) return '';
          const parsed = new Date(raw);
          if (Number.isNaN(parsed.getTime())) return raw;
          return parsed.toLocaleString(undefined, {
            dateStyle: 'medium',
            timeStyle: 'medium'
          });
        }

        function discoveredValuesForColumn(columnName) {
          const values = [];
          const seen = new Set();
          state.rows.forEach(row => {
            const value = rowValueForColumn(row, columnName, false).trim();
            if (!value) return;
            const key = value.toLowerCase();
            if (seen.has(key)) return;
            seen.add(key);
            values.push(value);
          });
          values.sort((left, right) => left.localeCompare(right, undefined, { sensitivity: 'base' }));
          return values;
        }

        // Render the fixed selection header so checkbox state is always available and non-movable.
        function renderSelectionHeaderCell() {
          const th = document.createElement('th');
          th.className = 'selection-column';
          th.dataset.columnKey = SELECTION_COLUMN_KEY;
          th.textContent = displayColumnName(SELECTION_COLUMN_KEY);
          th.title = 'Selection checkbox state';
          headerRow.appendChild(th);
        }

        // Render the fixed selection filter with both/selected/unselected choices.
        function renderSelectionFilterCell() {
          const th = document.createElement('th');
          th.className = 'selection-column';
          const select = document.createElement('select');
          [
            { value: SELECTION_FILTER_BOTH, label: 'Both' },
            { value: SELECTION_FILTER_SELECTED, label: 'Selected' },
            { value: SELECTION_FILTER_UNSELECTED, label: 'Unselected' },
          ].forEach(optionSpec => {
            const option = document.createElement('option');
            option.value = optionSpec.value;
            option.textContent = optionSpec.label;
            select.appendChild(option);
          });
          select.value = String(state.selectionFilter || SELECTION_FILTER_BOTH);
          select.addEventListener('click', event => {
            event.stopPropagation();
          });
          select.addEventListener('change', () => {
            state.selectionFilter = String(select.value || SELECTION_FILTER_BOTH);
            state.page = 1;
            renderBody();
          });
          th.appendChild(select);
          columnFilterRow.appendChild(th);
        }

        // Render one non-navigating selection checkbox cell for a row.
        function renderSelectionBodyCell(row, tr) {
          const td = document.createElement('td');
          td.className = 'selection-column';
          td.addEventListener('click', event => {
            event.stopPropagation();
          });
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.checked = isRowSelected(row);
          checkbox.setAttribute('aria-label', `Select ${String(row && row.filename ? row.filename : 'row')}`);
          checkbox.addEventListener('click', event => {
            event.stopPropagation();
          });
          checkbox.addEventListener('change', event => {
            setRowSelected(row, event.target && event.target.checked);
            state.page = 1;
            renderBody();
          });
          td.appendChild(checkbox);
          tr.appendChild(td);
        }

        function renderHeader() {
          headerRow.innerHTML = '';
          renderSelectionHeaderCell();
          state.columns.forEach(col => {
            const th = document.createElement('th');
            th.className = 'column-header';
            th.draggable = true;
            th.dataset.columnKey = col;
            th.textContent = displayColumnName(col);
            th.title = `${displayColumnName(col)} (click to sort, drag to reorder)`;
            th.addEventListener('click', () => {
              if (skipSortClickForColumn && skipSortClickForColumn === col) {
                skipSortClickForColumn = '';
                return;
              }
              if (state.sortKey === col) {
                state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
              } else {
                state.sortKey = col;
                state.sortDir = 'asc';
              }
              renderBody();
            });
            th.addEventListener('dragstart', event => {
              draggingColumnKey = col;
              th.classList.add('dragging');
              if (event.dataTransfer) {
                event.dataTransfer.effectAllowed = 'move';
                event.dataTransfer.setData('text/plain', col);
              }
            });
            th.addEventListener('dragover', event => {
              if (!draggingColumnKey || draggingColumnKey === col) return;
              event.preventDefault();
              th.classList.add('drag-over');
              if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
            });
            th.addEventListener('dragleave', () => {
              th.classList.remove('drag-over');
            });
            th.addEventListener('drop', event => {
              event.preventDefault();
              th.classList.remove('drag-over');
              const dragKey = draggingColumnKey;
              if (!dragKey || dragKey === col) return;
              const rect = th.getBoundingClientRect();
              const placeAfter = (event.clientX - rect.left) > (rect.width / 2);
              const moved = moveColumnRelativeToTarget(dragKey, col, placeAfter);
              if (!moved) return;
              skipSortClickForColumn = col;
              persistColumnOrder();
              renderHeader();
              renderBody();
            });
            th.addEventListener('dragend', () => {
              draggingColumnKey = '';
              th.classList.remove('dragging');
              headerRow.querySelectorAll('.drag-over').forEach(item => {
                item.classList.remove('drag-over');
              });
            });
            headerRow.appendChild(th);
          });
          renderColumnFilterRow();
        }

        function renderColumnFilterRow() {
          if (!columnFilterRow) return;
          columnFilterRow.innerHTML = '';
          renderSelectionFilterCell();
          state.columns.forEach(col => {
            const th = document.createElement('th');
            const isDiscoveredSelectColumn = ['config_type', 'engine', 'version'].includes(col);
            if (isDiscoveredSelectColumn) {
              const select = document.createElement('select');
              const defaultOption = document.createElement('option');
              defaultOption.value = '';
              defaultOption.textContent = 'All';
              select.appendChild(defaultOption);
              discoveredValuesForColumn(col).forEach(value => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                select.appendChild(option);
              });
              select.value = String(state.columnFilters[col] || '');
              select.addEventListener('click', event => {
                event.stopPropagation();
              });
              select.addEventListener('change', () => {
                state.columnFilters[col] = String(select.value || '');
                state.page = 1;
                renderBody();
              });
              th.appendChild(select);
            } else {
              const input = document.createElement('input');
              input.type = 'text';
              input.placeholder = `Filter ${displayColumnName(col)}`;
              input.value = String(state.columnFilters[col] || '');
              input.addEventListener('click', event => {
                event.stopPropagation();
              });
              input.addEventListener('input', () => {
                state.columnFilters[col] = input.value;
                state.page = 1;
                renderBody();
              });
              th.appendChild(input);
            }
            columnFilterRow.appendChild(th);
          });
        }

        function renderFeatureMenuItems(items) {
          if (!featureMenuGroup || !featureMenuSelect) return;
          const list = Array.isArray(items) ? items : [];
          const currentUrl = new URL(window.location.href);
          const normalizePath = value => {
            const raw = String(value || '').trim();
            if (!raw) return '/';
            return raw.length > 1 ? raw.replace(/\/+$/, '') : raw;
          };
          const isCurrentFeatureUrl = url => {
            try {
              const targetUrl = new URL(url, window.location.origin);
              const sameOrigin = targetUrl.origin === currentUrl.origin;
              const samePath = normalizePath(targetUrl.pathname) === normalizePath(currentUrl.pathname);
              return sameOrigin && samePath;
            } catch (_err) {
              return false;
            }
          };
          const validItems = list.filter(item => {
            const label = String(item && item.label ? item.label : '').trim();
            const url = String(item && item.url ? item.url : '').trim();
            return Boolean(label && url);
          });
          const navigableItems = validItems.filter(item => !isCurrentFeatureUrl(item.url));
          featureMenuSelect.innerHTML = '';
          const placeholder = document.createElement('option');
          placeholder.value = '';
          placeholder.textContent = 'Open...';
          featureMenuSelect.appendChild(placeholder);
          validItems.forEach(item => {
            const label = String(item && item.label ? item.label : '').trim();
            const url = String(item && item.url ? item.url : '').trim();
            const target = String(item && item.target ? item.target : '_self').trim() || '_self';
            if (!label || !url) return;
            const option = document.createElement('option');
            option.value = url;
            option.textContent = label;
            option.dataset.target = target;
            featureMenuSelect.appendChild(option);
          });
          const hasItems = navigableItems.length > 0;
          featureMenuGroup.classList.toggle('hidden', !hasItems);
          featureMenuSelect.selectedIndex = 0;
        }

        function onFeatureMenuChange() {
          if (!featureMenuSelect) return;
          const selected = featureMenuSelect.options[featureMenuSelect.selectedIndex];
          if (!selected) return;
          const url = String(selected.value || '').trim();
          if (!url) return;
          const target = String(selected.dataset.target || '_self').trim() || '_self';
          if (target === '_blank') {
            window.open(url, '_blank', 'noopener,noreferrer');
          } else {
            window.location.assign(url);
          }
          featureMenuSelect.selectedIndex = 0;
        }

        async function loadUiFeatures() {
          if (!featureMenuGroup || !featureMenuSelect) return;
          try {
            const payload = await api.getUiFeatures();
            state.uiFeatureItems = Array.isArray(payload.items) ? payload.items : [];
            renderFeatureMenuItems(state.uiFeatureItems);
            const configEditorItem = state.uiFeatureItems.find(item => {
              return String(item && item.entry_point ? item.entry_point : '').trim() === __CATALOG_CONFIG_EDITOR_ENTRY_POINT__;
            });
            state.configEditorUrl = configEditorItem ? String(configEditorItem.url || '').trim() : '';
            state.configEditorAvailable = !!state.configEditorUrl;
          } catch (_err) {
            featureMenuGroup.classList.add('hidden');
          }
        }

        function configEditorLinkForRow(row) {
          if (!state.configEditorAvailable || !state.configEditorUrl) return '';
          const path = String(row && row.path ? row.path : '').trim();
          if (!path) return '';
          const targetUrl = new URL(state.configEditorUrl, window.location.origin);
          targetUrl.searchParams.set('source_path', path);
          return targetUrl.toString();
        }

        function closeReadonlyViewer() {
          if (!readonlyOverlay) return;
          readonlyOverlay.hidden = true;
          readonlyOverlay.classList.add('hidden');
          readonlyOverlay.setAttribute('aria-hidden', 'true');
        }

        async function openReadonlyViewer(row) {
          const path = String(row && row.path ? row.path : '').trim();
          const filename = String(row && row.filename ? row.filename : '').trim() || 'Config File Viewer';
          if (!path || !readonlyOverlay || !readonlyText || !readonlyPath || !readonlyTitle || !readonlyError) return;
          readonlyTitle.textContent = `Config File Viewer: ${filename}`;
          readonlyPath.textContent = path;
          readonlyText.value = '';
          readonlyError.textContent = '';
          readonlyError.classList.add('hidden');
          readonlyOverlay.hidden = false;
          readonlyOverlay.classList.remove('hidden');
          readonlyOverlay.setAttribute('aria-hidden', 'false');
          try {
            const payload = await api.getFileContent(path);
            readonlyText.value = String(payload && payload.text ? payload.text : '');
          } catch (err) {
            readonlyError.textContent = String(err && err.message ? err.message : err);
            readonlyError.classList.remove('hidden');
          }
          readonlyText.focus();
        }

        function renderBody() {
          const rows = sortedFilteredRows();
          const totalPages = Math.max(1, Math.ceil(rows.length / state.pageSize));
          if (state.page > totalPages) state.page = totalPages;
          const start = (state.page - 1) * state.pageSize;
          const pageRows = rows.slice(start, start + state.pageSize);
          body.innerHTML = '';
          pageRows.forEach(row => {
            const tr = document.createElement('tr');
            if (isRowSelected(row)) {
              tr.classList.add('is-selected');
            }
            const editorUrl = configEditorLinkForRow(row);
            if (row && row.path) {
              tr.classList.add('is-clickable');
              tr.title = editorUrl ? 'Open in Config Service' : 'View configuration file (read only)';
              tr.addEventListener('click', () => {
                if (editorUrl) {
                  window.location.assign(editorUrl);
                  return;
                }
                openReadonlyViewer(row);
              });
            }
            renderSelectionBodyCell(row, tr);
            state.columns.forEach(col => {
              const td = document.createElement('td');
              if (col === 'folder') td.textContent = row.folder || '';
              else if (col === 'filename') td.textContent = row.filename || '';
              else if (col === 'last_edited') td.textContent = formatCatalogTimestamp(row.last_edited || '');
              else td.textContent = (row.metadata && row.metadata[col]) || '';
              tr.appendChild(td);
            });
            body.appendChild(tr);
          });
          summary.textContent = `${rows.length} entries • ${state.selectedPaths.length} selected`;
          pageNum.textContent = String(state.page);
          syncSelectionActions();
        }

        async function loadRows(options = {}) {
          if (isLoadingRows) return;
          isLoadingRows = true;
          try {
            const payload = await api.getFiles();
            if (options.autoRefresh === true && state.selectedPaths.length > 0) {
              return;
            }
            const availableColumns = normalizeColumns(payload.columns);
            state.columns = sanitizeColumnOrder(
              readStoredColumnOrder(availableColumns),
              availableColumns
            );
            state.columnFilters = normalizeColumnFilters(state.columnFilters, state.columns);
            state.rows = Array.isArray(payload.rows) ? payload.rows : [];
            reconcileSelectedPaths(state.rows);
            renderHeader();
            renderBody();
          } catch (err) {
            summary.textContent = 'Failed to load catalog data';
            if (window.console && typeof window.console.warn === 'function') {
              window.console.warn('Failed to load catalog rows', err);
            }
          } finally {
            isLoadingRows = false;
          }
        }

        function startCatalogRefreshTimer() {
          if (refreshTimer || UI_REFRESH_SECONDS <= 0) return;
          refreshTimer = window.setInterval(() => {
            if (state.selectedPaths.length > 0) {
              return;
            }
            void loadRows({ autoRefresh: true });
          }, UI_REFRESH_SECONDS * 1000);
        }

        filterInput.addEventListener('input', () => {
          state.filter = filterInput.value;
          state.page = 1;
          renderBody();
        });
        pageSizeInput.addEventListener('change', () => {
          const next = parseInt(pageSizeInput.value, 10);
          if (!Number.isNaN(next) && next >= 5) state.pageSize = next;
          state.page = 1;
          renderBody();
        });
        document.getElementById('catalogPrev').addEventListener('click', () => {
          state.page = Math.max(1, state.page - 1);
          renderBody();
        });
        document.getElementById('catalogNext').addEventListener('click', () => {
          const rows = sortedFilteredRows();
          const totalPages = Math.max(1, Math.ceil(rows.length / state.pageSize));
          state.page = Math.min(totalPages, state.page + 1);
          renderBody();
        });
        if (applySelectionButton) {
          applySelectionButton.addEventListener('click', () => {
            void applySelectedRows();
          });
        }
        if (featureMenuSelect) {
          featureMenuSelect.addEventListener('change', onFeatureMenuChange);
        }
        [document.getElementById('catalogReadonlyCloseTop'), document.getElementById('catalogReadonlyCloseBottom')].forEach(button => {
          if (!button) return;
          button.addEventListener('click', closeReadonlyViewer);
        });
        if (readonlyOverlay) {
          readonlyOverlay.addEventListener('click', (event) => {
            if (event.target === readonlyOverlay) {
              closeReadonlyViewer();
            }
          });
        }
        document.addEventListener('keydown', (event) => {
          if (event.key === 'Escape' && readonlyOverlay && !readonlyOverlay.classList.contains('hidden')) {
            closeReadonlyViewer();
          }
        });
        api.installGlobalUiErrorHandlers();
        syncSelectionActions();
        loadUiFeatures().then(() => loadRows()).then(startCatalogRefreshTimer);
      })();
