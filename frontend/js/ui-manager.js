import { money, dateTime } from './utils.js';

export function setStatus(element, text, tone = "neutral") {
    element.textContent = text;
    element.style.color = tone === "ok" ? "var(--green)" : tone === "error" ? "var(--red)" : "var(--muted)";
}

export function updateTable(container, data, renderer) {
    container.innerHTML = "";
    if (!data || data.length === 0) {
        const tr = document.createElement("tr");
        const columns = Number(container.dataset.columns || 1);
        const emptyMessage = container.dataset.emptyMessage || "Sin datos";
        tr.innerHTML = `<td colspan="${columns}" class="empty-table-cell">${emptyMessage}</td>`;
        container.appendChild(tr);
        return;
    }

    data.forEach(item => {
        const tr = document.createElement("tr");
        tr.innerHTML = renderer(item);
        container.appendChild(tr);
    });
}

export function toggleScreens(screens, buttons, activeName) {
    screens.forEach(s => s.classList.toggle("active", s.id === `screen-${activeName}`));
    buttons.forEach(b => b.classList.toggle("active", b.dataset.screen === activeName));
}