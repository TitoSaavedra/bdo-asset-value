import * as api from './api.js';
import * as ui from './ui-manager.js';
import { money, dateTime } from './utils.js';
import { renderChart } from './chart-engine.js';

// Selección de elementos
const elements = {
    status: document.getElementById("status"),
    historyBody: document.getElementById("historyBody"),
    chart: document.getElementById("chart"),
    // ... rest of elements
};

let state = { dashboard: null };

async function refresh() {
    state.dashboard = await api.getDashboardData();
    render();
}

function render() {
    const { dashboard } = state;
    if (!dashboard) return;

    // Actualizar totales
    document.getElementById("mMarket").textContent = money(dashboard.latest.market_silver);
    
    // Renderizar tablas usando el helper de UI
    ui.updateTable(elements.historyBody, [...dashboard.records].reverse(), (item) => `
        <td>${dateTime(item.captured_at)}</td>
        <td>${money(item.market_silver)}</td>
        <td class="badge-green">${money(item.total_with_warehouses)}</td>
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

document.getElementById("refreshBtn").addEventListener("click", refresh);

// Inicio
refresh();