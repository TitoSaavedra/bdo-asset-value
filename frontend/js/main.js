import * as api from './api.js';
import * as ui from './ui-manager.js';
import { money, dateTime } from './utils.js';
import { renderChart } from './chart-engine.js';

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
    refreshBtn: document.getElementById("refreshBtn"),
};

let state = { dashboard: null, historyRange: "all" };


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
        return { text: "Pendiente", className: "status-pending" };
    }

    const now = new Date();
    const updatedAt = new Date(item.last_captured_at);
    const diffHours = (now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60);

    if (diffHours <= 24) {
        return { text: "Actualizado", className: "status-updated" };
    }

    if (diffHours <= 72) {
        return { text: "Por revisar", className: "status-review" };
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
    render();
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

    ui.setStatus(elements.status, `Valor manual guardado para ${warehouse}.`, 'ok');
    await refresh();
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

    const filteredHistoryRecords = filterHistoryRecords(allRecords, state.historyRange);

    ui.updateTable(elements.historyBody, [...filteredHistoryRecords].reverse(), (item) => `
        <td>${dateTime(item.captured_at)}</td>
        <td>${item.source || '-'}</td>
        <td>${money(item.market_silver)}</td>
        <td>${money(item.inventory_silver)}</td>
        <td>${money(item.preorder_silver)}</td>
        <td>${money(item.total_without_warehouses)}</td>
        <td class="badge-green">${money(item.total_with_warehouses)}</td>
    `);

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

    ui.updateTable(elements.snapshotsBody, [...(dashboard.warehouse_snapshots || [])].reverse(), (item) => `
        <td>${dateTime(item.captured_at)}</td>
        <td>${item.warehouse}</td>
        <td>${money(item.market_silver)}</td>
    `);

    renderChart(elements.chart, dashboard.records, dashboard.settings);
}

// Event Listeners
document.querySelectorAll(".menu button").forEach(btn => {
    btn.addEventListener("click", () => ui.toggleScreens(
        document.querySelectorAll(".screen"), 
        document.querySelectorAll(".menu button"), 
        btn.dataset.screen
    ));
});

if (elements.refreshBtn) {
    elements.refreshBtn.addEventListener("click", refresh);
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
        button.addEventListener("click", () => {
            state.historyRange = button.dataset.historyRange || "all";

            elements.historyFilters.forEach((filterButton) => {
                filterButton.classList.toggle("active", filterButton === button);
            });

            render();
        });
    });
}

bindInlineTableEditing();
refresh();
connectUpdatesSocket();