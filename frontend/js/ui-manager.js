import { money, dateTime } from './utils.js';

export function setStatus(element, text, tone = "neutral") {
    element.textContent = text;
    element.style.color = tone === "ok" ? "var(--green)" : tone === "error" ? "var(--red)" : "var(--muted)";
}

export function updateTable(container, data, renderer) {
    container.innerHTML = "";
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