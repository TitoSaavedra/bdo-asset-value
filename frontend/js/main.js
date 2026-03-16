import * as api from './api.js';
import * as ui from './ui-manager.js';
import { money, dateTime } from './utils.js';
import { renderChart } from './chart-engine.js';
import { loadScreenViews } from './view-loader.js';

await loadScreenViews();

const elements = {
    status: document.getElementById("status"),
    historyBody: document.getElementById("historyBody"),
    warehouseSummaryBody: document.getElementById("warehouseSummaryBody"),
    warehouseListBody: document.getElementById("warehouseListBody"),
    warehouseMissingInfo: document.getElementById("warehouseMissingInfo"),
    snapshotsBody: document.getElementById("snapshotsBody"),
    chart: document.getElementById("chart"),
    market: document.getElementById("mMarket"),
    marketDelta: document.getElementById("mMarketDelta"),
    inventory: document.getElementById("mInventory"),
    inventoryDelta: document.getElementById("mInventoryDelta"),
    preorder: document.getElementById("mPreorder"),
    preorderDelta: document.getElementById("mPreorderDelta"),
    total: document.getElementById("mTotal"),
    totalHint: document.getElementById("mTotalHint"),
    totalDelta: document.getElementById("mTotalDelta"),
    includeWarehousesToggle: document.getElementById("includeWarehousesToggle"),
    historyFilters: document.querySelectorAll("[data-history-range]"),
    historyPagination: document.getElementById("historyPagination"),
    historyPrevBtn: document.getElementById("historyPrevBtn"),
    historyNextBtn: document.getElementById("historyNextBtn"),
    historyPageInfo: document.getElementById("historyPageInfo"),
    snapshotsPagination: document.getElementById("snapshotsPagination"),
    snapshotsPrevBtn: document.getElementById("snapshotsPrevBtn"),
    snapshotsNextBtn: document.getElementById("snapshotsNextBtn"),
    snapshotsPageInfo: document.getElementById("snapshotsPageInfo"),
    chartRangeFilters: document.querySelectorAll("[data-chart-range]"),
    seriesToggles: document.querySelectorAll(".series-toggle"),
    toastRegion: document.getElementById("toastRegion"),
    refreshBtn: document.getElementById("refreshBtn"),
    themeSelect: document.getElementById("themeSelect"),
    refreshMetricsBtn: document.getElementById("refreshMetricsBtn"),
    metricDashboardLastMs: document.getElementById("metricDashboardLastMs"),
    metricDashboardAvgMs: document.getElementById("metricDashboardAvgMs"),
    metricPayloadBytes: document.getElementById("metricPayloadBytes"),
    metricWritesPerMinute: document.getElementById("metricWritesPerMinute"),
    metricsBody: document.getElementById("metricsBody"),
    metricsUpdatedAt: document.getElementById("metricsUpdatedAt"),
};

const CHART_PREFS_KEY = "bdo_asset_chart_prefs";
const THEME_PREFS_KEY = "bdo_asset_theme";
const TABLE_PAGE_SIZE = 20;
const ALLOWED_THEMES = new Set(["desert", "midnight", "light"]);
const DEFAULT_VISIBLE_SERIES = {
    total: true,
    market: true,
    inventory: true,
    preorder: true,
    warehouses: true,
};

let state = {
    dashboard: null,
    historyRange: "all",
    historyPage: 1,
    historyPageData: null,
    snapshotsPage: 1,
    snapshotsPageData: null,
    chartRange: "all",
    theme: "desert",
    visibleSeries: { ...DEFAULT_VISIBLE_SERIES },
    recentlyUpdatedWarehouse: null,
};


function updatePaginationControls(kind, pageData) {
    const isHistory = kind === "history";
    const container = isHistory ? elements.historyPagination : elements.snapshotsPagination;
    const prevBtn = isHistory ? elements.historyPrevBtn : elements.snapshotsPrevBtn;
    const nextBtn = isHistory ? elements.historyNextBtn : elements.snapshotsNextBtn;
    const pageInfo = isHistory ? elements.historyPageInfo : elements.snapshotsPageInfo;

    if (!container || !prevBtn || !nextBtn || !pageInfo) {
        return;
    }

    const totalItems = Number(pageData?.total || 0);
    const limit = Math.max(1, Number(pageData?.limit || TABLE_PAGE_SIZE));
    const offset = Math.max(0, Number(pageData?.offset || 0));
    const totalPages = Math.max(1, Math.ceil(totalItems / limit));
    const currentPage = Math.min(totalPages, Math.floor(offset / limit) + 1);

    container.hidden = totalItems <= limit;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    pageInfo.textContent = `Página ${currentPage} / ${totalPages} · ${totalItems} items`;
}


function applyTheme(themeName) {
    const safeTheme = ALLOWED_THEMES.has(themeName) ? themeName : "desert";
    state.theme = safeTheme;

    document.body.dataset.theme = safeTheme;

    if (elements.themeSelect) {
        elements.themeSelect.value = safeTheme;
    }
}


function loadThemePreference() {
    try {
        const savedTheme = localStorage.getItem(THEME_PREFS_KEY);
        applyTheme(savedTheme || "desert");
    } catch (_error) {
        applyTheme("desert");
    }
}


function saveThemePreference() {
    localStorage.setItem(THEME_PREFS_KEY, state.theme);
}


function loadChartPreferences() {
    try {
        const raw = localStorage.getItem(CHART_PREFS_KEY);
        if (!raw) {
            return;
        }

        const parsed = JSON.parse(raw);
        state.chartRange = parsed.chartRange || "all";
        state.visibleSeries = {
            ...DEFAULT_VISIBLE_SERIES,
            ...(parsed.visibleSeries || {}),
        };
    } catch (_error) {
        state.chartRange = "all";
        state.visibleSeries = { ...DEFAULT_VISIBLE_SERIES };
    }
}


function saveChartPreferences() {
    localStorage.setItem(CHART_PREFS_KEY, JSON.stringify({
        chartRange: state.chartRange,
        visibleSeries: state.visibleSeries,
    }));
}


function showToast(message, tone = "ok") {
    if (!elements.toastRegion) {
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${tone}`;
    toast.textContent = message;
    elements.toastRegion.appendChild(toast);

    window.setTimeout(() => {
        toast.classList.add("toast-out");
        window.setTimeout(() => toast.remove(), 240);
    }, 2200);
}


function syncChartControls() {
    if (elements.chartRangeFilters) {
        elements.chartRangeFilters.forEach((button) => {
            button.classList.toggle("active", button.dataset.chartRange === state.chartRange);
        });
    }

    if (elements.seriesToggles) {
        elements.seriesToggles.forEach((toggle) => {
            const key = toggle.dataset.seriesKey;
            toggle.checked = state.visibleSeries[key] !== false;
            const legendItem = toggle.closest('.legend-item');
            if (legendItem) {
                legendItem.classList.toggle('legend-disabled', !toggle.checked);
            }
        });
    }
}


function escapeAttribute(value) {
    return String(value ?? "").replace(/"/g, "&quot;");
}


function renderEditableWarehouseValue(warehouse, marketSilver) {
    const safeWarehouse = escapeAttribute(warehouse);
    const numericValue = marketSilver === null || marketSilver === undefined ? "" : Number(marketSilver);
    const displayValue = marketSilver === null || marketSilver === undefined ? "Sin dato" : money(marketSilver);

    return `
        <button
            class="inline-edit-trigger"
            type="button"
            data-edit-kind="warehouse-market"
            data-warehouse="${safeWarehouse}"
            data-value="${numericValue}"
            aria-label="Editar valor manual de ${safeWarehouse}"
            title="Click para editar"
        >${displayValue}</button>
    `;
}


function formatRelativeTime(isoDate) {
    if (!isoDate) return "Sin actualización";

    const updateTime = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - updateTime.getTime();

    if (Number.isNaN(updateTime.getTime()) || diffMs < 0) {
        return "Hace un momento";
    }

    const diffSeconds = Math.floor(diffMs / 1000);
    if (diffSeconds < 60) {
        return `Hace ${diffSeconds}s`;
    }

    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) {
        return `Hace ${diffMinutes} min`;
    }

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) {
        return `Hace ${diffHours} h`;
    }

    const diffDays = Math.floor(diffHours / 24);
    return `Hace ${diffDays} días`;
}

function getRangeStartDate(range) {
    const now = new Date();

    if (range === "today") {
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }

    if (range === "7d") {
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    }

    if (range === "30d") {
        return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }

    return null;
}

function filterHistoryRecords(records, range) {
    const startDate = getRangeStartDate(range);
    if (!startDate) {
        return records;
    }

    return records.filter((record) => new Date(record.captured_at) >= startDate);
}

function getPreviousRecord(records) {
    if (!records || records.length < 2) {
        return null;
    }

    return records[records.length - 2];
}

function applyDelta(element, currentValue, previousValue) {
    if (!element) return;

    if (previousValue === null || previousValue === undefined) {
        element.textContent = "Sin referencia";
        element.className = "metric-delta delta-neutral";
        return;
    }

    const delta = Number(currentValue || 0) - Number(previousValue || 0);
    if (delta > 0) {
        element.textContent = `▲ ${money(delta)} vs anterior`;
        element.className = "metric-delta delta-up";
        return;
    }

    if (delta < 0) {
        element.textContent = `▼ ${money(Math.abs(delta))} vs anterior`;
        element.className = "metric-delta delta-down";
        return;
    }

    element.textContent = "Sin cambios vs anterior";
    element.className = "metric-delta delta-neutral";
}

function getWarehouseBadge(item) {
    if (!item.updated || !item.last_captured_at) {
        return { text: "Desactualizado", className: "status-stale" };
    }

    const now = new Date();
    const updatedAt = new Date(item.last_captured_at);
    const diffHours = (now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60);

    if (!Number.isFinite(diffHours) || diffHours < 0) {
        return { text: "Desactualizado", className: "status-stale" };
    }

    if (diffHours <= 10) {
        return { text: "Actualizado", className: "status-updated" };
    }

    if (diffHours <= 16) {
        return { text: "Actualizado", className: "status-review" };
    }

    return { text: "Desactualizado", className: "status-stale" };
}

function connectUpdatesSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/updates`);

    socket.addEventListener('message', async (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload?.type === 'asset_history_updated') {
                await refresh();
            }
        } catch (error) {
            console.error('Invalid WebSocket payload', error);
        }
    });

    socket.addEventListener('close', () => {
        setTimeout(connectUpdatesSocket, 2000);
    });
}

async function refresh() {
    state.dashboard = await api.getDashboardData();
    await Promise.all([
        loadHistoryPage(),
        loadSnapshotsPage(),
    ]);
    render();
}


async function loadHistoryPage() {
    const offset = (state.historyPage - 1) * TABLE_PAGE_SIZE;
    const pageData = await api.getHistoryPage(TABLE_PAGE_SIZE, offset, state.historyRange);
    state.historyPageData = pageData;

    const totalPages = Math.max(1, Math.ceil((pageData.total || 0) / TABLE_PAGE_SIZE));
    if (state.historyPage > totalPages) {
        state.historyPage = totalPages;
        return loadHistoryPage();
    }
}


async function loadSnapshotsPage() {
    const offset = (state.snapshotsPage - 1) * TABLE_PAGE_SIZE;
    const pageData = await api.getSnapshotsPage(TABLE_PAGE_SIZE, offset);
    state.snapshotsPageData = pageData;

    const totalPages = Math.max(1, Math.ceil((pageData.total || 0) / TABLE_PAGE_SIZE));
    if (state.snapshotsPage > totalPages) {
        state.snapshotsPage = totalPages;
        return loadSnapshotsPage();
    }
}


async function saveManualWarehouseValue(warehouse, marketSilver) {
    ui.setStatus(elements.status, `Guardando valor manual para ${warehouse}...`);
    const response = await api.postManualWarehouseValue({
        warehouse,
        market_silver: marketSilver,
    });

    if (!response.ok) {
        throw new Error('No se pudo guardar el valor manual del almacén');
    }

    state.recentlyUpdatedWarehouse = warehouse;
    ui.setStatus(elements.status, `Valor manual guardado para ${warehouse}.`, 'ok');
    showToast(`Guardado: ${warehouse}`, 'ok');
    await refresh();
}


function highlightRecentlyUpdatedWarehouse() {
    if (!state.recentlyUpdatedWarehouse) {
        return;
    }

    const targetWarehouse = state.recentlyUpdatedWarehouse;
    const matchingButtons = document.querySelectorAll(`.inline-edit-trigger[data-warehouse="${CSS.escape(targetWarehouse)}"]`);

    matchingButtons.forEach((button) => {
        button.classList.add("inline-edit-saved");
        window.setTimeout(() => button.classList.remove("inline-edit-saved"), 1500);
    });

    state.recentlyUpdatedWarehouse = null;
}


function bindInlineTableEditing() {
    if (document.body.dataset.inlineEditBound === '1') {
        return;
    }

    document.body.addEventListener('click', (event) => {
        const trigger = event.target.closest('.inline-edit-trigger');
        if (!trigger) {
            return;
        }

        if (trigger.dataset.editKind !== 'warehouse-market') {
            return;
        }

        event.preventDefault();

        if (trigger.dataset.editing === '1') {
            return;
        }

        trigger.dataset.editing = '1';

        const warehouse = trigger.dataset.warehouse;
        const originalRaw = trigger.dataset.value || '';
        const originalValue = originalRaw === '' ? 0 : Number(originalRaw);

        const input = document.createElement('input');
        input.type = 'number';
        input.min = '0';
        input.step = '1';
        input.className = 'inline-edit-input';
        input.value = String(originalValue);

        const finalize = async (mode) => {
            if (trigger.dataset.finalizing === '1') {
                return;
            }

            trigger.dataset.finalizing = '1';

            if (mode === 'cancel') {
                trigger.style.display = '';
                input.remove();
                trigger.dataset.editing = '0';
                trigger.dataset.finalizing = '0';
                return;
            }

            const parsed = Number(input.value);
            if (!Number.isFinite(parsed) || parsed < 0) {
                ui.setStatus(elements.status, 'Ingresa un número válido (0 o mayor).', 'error');
                input.focus();
                input.select();
                trigger.dataset.finalizing = '0';
                return;
            }

            if (parsed === originalValue) {
                trigger.style.display = '';
                input.remove();
                trigger.dataset.editing = '0';
                trigger.dataset.finalizing = '0';
                return;
            }

            try {
                await saveManualWarehouseValue(warehouse, Math.trunc(parsed));
            } catch (error) {
                ui.setStatus(elements.status, error.message || 'Error guardando valor manual.', 'error');
                showToast(error.message || 'No se pudo guardar.', 'error');
            } finally {
                trigger.style.display = '';
                input.remove();
                trigger.dataset.editing = '0';
                trigger.dataset.finalizing = '0';
            }
        };

        input.addEventListener('keydown', (keyEvent) => {
            if (keyEvent.key === 'Enter') {
                keyEvent.preventDefault();
                finalize('save');
            }

            if (keyEvent.key === 'Escape') {
                keyEvent.preventDefault();
                finalize('cancel');
            }
        });

        input.addEventListener('blur', () => finalize('save'));

        trigger.style.display = 'none';
        trigger.insertAdjacentElement('afterend', input);
        input.focus();
        input.select();
    });

    document.body.dataset.inlineEditBound = '1';
}

function render() {
    const { dashboard } = state;
    if (!dashboard) return;
    const allRecords = dashboard.records || [];
    const latest = dashboard.latest || {
        market_silver: 0,
        inventory_silver: 0,
        preorder_silver: 0,
        total_without_warehouses: 0,
        total_with_warehouses: 0,
    };
    const previous = getPreviousRecord(allRecords);

    const includeWarehouses = Boolean(dashboard.settings?.include_warehouses_in_total);
    const totalValue = includeWarehouses
        ? (latest.total_with_warehouses || 0)
        : (latest.total_without_warehouses || 0);

    elements.market.textContent = money(latest.market_silver || 0);
    elements.inventory.textContent = money(latest.inventory_silver || 0);
    elements.preorder.textContent = money(latest.preorder_silver || 0);
    elements.total.textContent = money(totalValue);
    elements.totalHint.textContent = includeWarehouses ? "Incluye almacenes" : "Sin almacenes";

    applyDelta(elements.marketDelta, latest.market_silver, previous?.market_silver);
    applyDelta(elements.inventoryDelta, latest.inventory_silver, previous?.inventory_silver);
    applyDelta(elements.preorderDelta, latest.preorder_silver, previous?.preorder_silver);
    applyDelta(
        elements.totalDelta,
        includeWarehouses ? latest.total_with_warehouses : latest.total_without_warehouses,
        includeWarehouses ? previous?.total_with_warehouses : previous?.total_without_warehouses,
    );

    if (elements.includeWarehousesToggle) {
        elements.includeWarehousesToggle.checked = includeWarehouses;
    }

    const filteredChartRecords = filterHistoryRecords(allRecords, state.chartRange);

    const historyItems = state.historyPageData?.items || [];
    ui.updateTable(elements.historyBody, historyItems, (item) => `
        <td>${dateTime(item.captured_at)}</td>
        <td>${item.source || '-'}</td>
        <td>${money(item.market_silver)}</td>
        <td>${money(item.inventory_silver)}</td>
        <td>${money(item.preorder_silver)}</td>
        <td>${money(item.total_without_warehouses)}</td>
        <td class="badge-green">${money(item.total_with_warehouses)}</td>
    `);
    updatePaginationControls("history", state.historyPageData || { total: 0, limit: TABLE_PAGE_SIZE, offset: 0 });

    const warehouseRows = dashboard.warehouse_list || [];
    const warehouseStatusRows = dashboard.warehouse_status_list || [];
    const missingWarehouses = dashboard.missing_warehouses || [];

    if (elements.warehouseMissingInfo) {
        if (missingWarehouses.length === 0) {
            elements.warehouseMissingInfo.textContent = "Todos los almacenes conocidos están actualizados.";
        } else {
            elements.warehouseMissingInfo.textContent = `Faltan ${missingWarehouses.length} almacenes por actualizar: ${missingWarehouses.join(', ')}`;
        }
    }
    ui.updateTable(elements.warehouseSummaryBody, warehouseRows, (item) => `
        <td>${item.warehouse}</td>
        <td>${renderEditableWarehouseValue(item.warehouse, item.market_silver)}</td>
    `);

    ui.updateTable(elements.warehouseListBody, warehouseStatusRows, (item) => `
        <td>${item.warehouse}</td>
        <td>${renderEditableWarehouseValue(item.warehouse, item.market_silver)}</td>
        <td>${item.last_captured_at ? dateTime(item.last_captured_at) : '-'}</td>
        <td>
            <span class="status-pill ${getWarehouseBadge(item).className}">${getWarehouseBadge(item).text}</span>
            <span class="status-time">${item.updated ? formatRelativeTime(item.last_captured_at) : 'Sin actualización'}</span>
        </td>
    `);

    const snapshotItems = state.snapshotsPageData?.items || [];
    ui.updateTable(elements.snapshotsBody, snapshotItems, (item) => `
        <td>${dateTime(item.captured_at)}</td>
        <td>${item.warehouse}</td>
        <td>${money(item.market_silver)}</td>
    `);
    updatePaginationControls("snapshots", state.snapshotsPageData || { total: 0, limit: TABLE_PAGE_SIZE, offset: 0 });

    syncChartControls();
    renderChart(elements.chart, filteredChartRecords, dashboard.settings, {
        visibleSeries: state.visibleSeries,
    });
    highlightRecentlyUpdatedWarehouse();
}


function bindChartRangeFilters() {
    if (!elements.chartRangeFilters) {
        return;
    }

    elements.chartRangeFilters.forEach((button) => {
        button.addEventListener("click", () => {
            state.chartRange = button.dataset.chartRange || "all";
            saveChartPreferences();
            render();
        });
    });
}


function bindChartSeriesToggles() {
    if (!elements.seriesToggles) {
        return;
    }

    elements.seriesToggles.forEach((toggle) => {
        toggle.addEventListener("change", () => {
            const key = toggle.dataset.seriesKey;
            state.visibleSeries[key] = toggle.checked;

            const enabledCount = Object.values(state.visibleSeries).filter(Boolean).length;
            if (enabledCount === 0) {
                state.visibleSeries[key] = true;
                toggle.checked = true;
                showToast("Debe quedar al menos una serie visible.", "error");
                return;
            }

            saveChartPreferences();
            render();
        });
    });
}


function bindThemeSelector() {
    if (!elements.themeSelect) {
        return;
    }

    elements.themeSelect.addEventListener("change", () => {
        applyTheme(elements.themeSelect.value);
        saveThemePreference();

        if (state.dashboard) {
            render();
        }
    });
}


function formatBytes(bytes) {
    const value = Number(bytes || 0);
    if (value < 1024) return `${value} B`;
    if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
    return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}


async function refreshMetricsPanel() {
    if (!elements.metricDashboardLastMs || !elements.metricsBody) {
        return;
    }

    const metrics = await api.getMetrics();

    elements.metricDashboardLastMs.textContent = `${Number(metrics.dashboard_render_ms_last || 0).toFixed(1)} ms`;
    elements.metricDashboardAvgMs.textContent = `${Number(metrics.dashboard_render_ms_avg || 0).toFixed(1)} ms`;
    elements.metricPayloadBytes.textContent = formatBytes(metrics.dashboard_payload_bytes_last || 0);
    elements.metricWritesPerMinute.textContent = String(metrics.writes_per_minute || 0);

    ui.updateTable(elements.metricsBody, [
        { key: "Dashboard calls", value: metrics.dashboard_calls || 0 },
        { key: "Writes total", value: metrics.writes_total || 0 },
        { key: "Payload último", value: formatBytes(metrics.dashboard_payload_bytes_last || 0) },
        { key: "Render último", value: `${Number(metrics.dashboard_render_ms_last || 0).toFixed(1)} ms` },
        { key: "Render promedio", value: `${Number(metrics.dashboard_render_ms_avg || 0).toFixed(1)} ms` },
        { key: "Writes/min", value: metrics.writes_per_minute || 0 },
    ], (item) => `
        <td>${item.key}</td>
        <td>${item.value}</td>
    `);

    if (elements.metricsUpdatedAt) {
        elements.metricsUpdatedAt.textContent = `Actualizado: ${new Date().toLocaleTimeString()}`;
    }
}


function bindTablePagination() {
    if (elements.historyPrevBtn) {
        elements.historyPrevBtn.addEventListener("click", async () => {
            state.historyPage = Math.max(1, state.historyPage - 1);
            await loadHistoryPage();
            render();
        });
    }

    if (elements.historyNextBtn) {
        elements.historyNextBtn.addEventListener("click", async () => {
            state.historyPage += 1;
            await loadHistoryPage();
            render();
        });
    }

    if (elements.snapshotsPrevBtn) {
        elements.snapshotsPrevBtn.addEventListener("click", async () => {
            state.snapshotsPage = Math.max(1, state.snapshotsPage - 1);
            await loadSnapshotsPage();
            render();
        });
    }

    if (elements.snapshotsNextBtn) {
        elements.snapshotsNextBtn.addEventListener("click", async () => {
            state.snapshotsPage += 1;
            await loadSnapshotsPage();
            render();
        });
    }
}

// Event Listeners
document.querySelectorAll(".menu button").forEach((btn) => {
    btn.addEventListener("click", async () => {
        ui.toggleScreens(
            document.querySelectorAll(".screen"),
            document.querySelectorAll(".menu button"),
            btn.dataset.screen,
        );

        if (btn.dataset.screen === 'metrics') {
            await refreshMetricsPanel();
        }
    });
});

if (elements.refreshBtn) {
    elements.refreshBtn.addEventListener("click", refresh);
}

if (elements.refreshMetricsBtn) {
    elements.refreshMetricsBtn.addEventListener("click", refreshMetricsPanel);
}

if (elements.includeWarehousesToggle) {
    elements.includeWarehousesToggle.addEventListener("change", async (event) => {
        const target = event.target;
        await api.postToggleWarehouses(target.checked);
        await refresh();
    });
}

if (elements.historyFilters) {
    elements.historyFilters.forEach((button) => {
        button.addEventListener("click", async () => {
            state.historyRange = button.dataset.historyRange || "all";
            state.historyPage = 1;

            elements.historyFilters.forEach((filterButton) => {
                filterButton.classList.toggle("active", filterButton === button);
            });

            await loadHistoryPage();
            render();
        });
    });
}

loadThemePreference();
loadChartPreferences();
bindInlineTableEditing();
bindChartRangeFilters();
bindChartSeriesToggles();
bindThemeSelector();
bindTablePagination();
refresh();
refreshMetricsPanel();
connectUpdatesSocket();