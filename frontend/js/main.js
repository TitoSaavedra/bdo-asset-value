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
    inventory: document.getElementById("mInventory"),
    preorder: document.getElementById("mPreorder"),
    total: document.getElementById("mTotal"),
    totalHint: document.getElementById("mTotalHint"),
    includeWarehousesToggle: document.getElementById("includeWarehousesToggle"),
    refreshBtn: document.getElementById("refreshBtn"),
};

let state = { dashboard: null };


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

function render() {
    const { dashboard } = state;
    if (!dashboard) return;
    const latest = dashboard.latest || {
        market_silver: 0,
        inventory_silver: 0,
        preorder_silver: 0,
        total_without_warehouses: 0,
        total_with_warehouses: 0,
    };

    const includeWarehouses = Boolean(dashboard.settings?.include_warehouses_in_total);
    const totalValue = includeWarehouses
        ? (latest.total_with_warehouses || 0)
        : (latest.total_without_warehouses || 0);

    elements.market.textContent = money(latest.market_silver || 0);
    elements.inventory.textContent = money(latest.inventory_silver || 0);
    elements.preorder.textContent = money(latest.preorder_silver || 0);
    elements.total.textContent = money(totalValue);
    elements.totalHint.textContent = includeWarehouses ? "Incluye almacenes" : "Sin almacenes";

    if (elements.includeWarehousesToggle) {
        elements.includeWarehousesToggle.checked = includeWarehouses;
    }

    ui.updateTable(elements.historyBody, [...dashboard.records].reverse(), (item) => `
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
        <td>${money(item.market_silver)}</td>
    `);

    ui.updateTable(elements.warehouseListBody, warehouseStatusRows, (item) => `
        <td>${item.warehouse}</td>
        <td>${item.market_silver === null ? '-' : money(item.market_silver)}</td>
        <td>${item.last_captured_at ? dateTime(item.last_captured_at) : '-'}</td>
        <td>${item.updated ? formatRelativeTime(item.last_captured_at) : 'Pendiente'}</td>
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

refresh();
connectUpdatesSocket();