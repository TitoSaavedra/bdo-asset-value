import { compact, shortDate } from './utils.js';

/**
 * Renderiza el gráfico de evolución de plata en el canvas.
 */
export function renderChart(canvas, records, settings) {
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    // Ajuste de resolución para pantallas High DPI (Retina)
    const width = Math.max(320, Math.floor(rect.width * dpr));
    const height = Math.max(280, Math.floor(rect.height * dpr));
    
    if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!records || records.length === 0) {
        ctx.fillStyle = "rgba(246,236,214,0.72)";
        ctx.font = `${16 * dpr}px Inter, Segoe UI, Arial`;
        ctx.textAlign = "center";
        ctx.fillText("Sin datos para graficar", canvas.width / 2, canvas.height / 2);
        return;
    }

    // --- Configuración de Escalas ---
    const include = !!settings.include_warehouses_in_total;
    const totalSeries = records.map(x => include ? x.total_with_warehouses : x.total_without_warehouses);
    const inventorySeries = records.map(x => x.inventory_silver || 0);
    const preorderSeries = records.map(x => x.preorder_silver || 0);

    const allValues = [...totalSeries, ...inventorySeries, ...preorderSeries];
    let min = Math.min(...allValues);
    let max = Math.max(...allValues);

    if (min === max) {
        min = min * 0.9;
        max = max * 1.1 + 1;
    }

    const padding = {
        top: 30 * dpr,
        right: 20 * dpr,
        bottom: 44 * dpr,
        left: 82 * dpr,
    };

    const plotW = canvas.width - padding.left - padding.right;
    const plotH = canvas.height - padding.top - padding.bottom;
    
    const range = max - min;
    const yMin = Math.max(0, min - range * 0.1);
    const yMax = max + range * 0.1;
    const yRange = yMax - yMin || 1;

    // --- Dibujo de Grid (Líneas horizontales) ---
    ctx.strokeStyle = "rgba(200,169,106,.16)";
    ctx.lineWidth = 1 * dpr;
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (plotH / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + plotW, y);
        ctx.stroke();
    }

    // --- Etiquetas Eje Y ---
    ctx.fillStyle = "rgba(185,171,141,.9)";
    ctx.font = `${12 * dpr}px Inter, Segoe UI, Arial`;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= 5; i++) {
        const value = yMax - (yRange / 5) * i;
        const y = padding.top + (plotH / 5) * i;
        ctx.fillText(compact(value), padding.left - 10 * dpr, y);
    }

    // --- Función interna para dibujar cada serie ---
    function drawSeries(values, strokeColor, fillColor) {
        const step = values.length === 1 ? 0 : plotW / (values.length - 1);
        const points = values.map((value, index) => ({
            x: padding.left + step * index,
            y: padding.top + plotH - ((value - yMin) / yRange) * plotH,
        }));

        if (points.length === 1) {
            ctx.beginPath();
            ctx.fillStyle = strokeColor;
            ctx.arc(points[0].x, points[0].y, 4 * dpr, 0, Math.PI * 2);
            ctx.fill();
            return;
        }

        // 1. Área rellena con gradiente
        const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + plotH);
        gradient.addColorStop(0, fillColor);
        gradient.addColorStop(1, "rgba(0,0,0,0)");

        ctx.beginPath();
        ctx.moveTo(points[0].x, padding.top + plotH);
        ctx.lineTo(points[0].x, points[0].y);
        
        for (let i = 1; i < points.length; i++) {
            const prev = points[i - 1];
            const curr = points[i];
            const cx = (prev.x + curr.x) / 2;
            ctx.quadraticCurveTo(prev.x, prev.y, cx, (prev.y + curr.y) / 2);
        }
        
        const last = points[points.length - 1];
        ctx.lineTo(last.x, last.y);
        ctx.lineTo(last.x, padding.top + plotH);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // 2. Línea de la serie
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
            const prev = points[i - 1];
            const curr = points[i];
            const cx = (prev.x + curr.x) / 2;
            ctx.quadraticCurveTo(prev.x, prev.y, cx, (prev.y + curr.y) / 2);
        }
        ctx.lineTo(last.x, last.y);
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 3 * dpr;
        ctx.stroke();
    }

    // Dibujar las 3 series (Total, Inventario, Pre-orders)
    drawSeries(totalSeries, "rgba(217,180,111,1)", "rgba(217,180,111,.18)");
    drawSeries(inventorySeries, "rgba(90,164,255,1)", "rgba(90,164,255,.15)");
    drawSeries(preorderSeries, "rgba(97,211,145,1)", "rgba(97,211,145,.15)");

    // --- Etiquetas Eje X (Fechas) ---
    const labelIndexes = computeLabelIndexes(records.length);
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = "rgba(185,171,141,.9)";
    ctx.font = `${11 * dpr}px Inter, Segoe UI, Arial`;
    
    const xStep = records.length === 1 ? 0 : plotW / (records.length - 1);
    for (const index of labelIndexes) {
        const x = padding.left + xStep * index;
        ctx.fillText(
            shortDate(records[index].captured_at),
            x,
            padding.top + plotH + 12 * dpr
        );
    }
}


function computeLabelIndexes(length) {
    if (length <= 6) return Array.from({ length }, (_, i) => i);
    const desired = 6;
    const step = (length - 1) / (desired - 1);
    const indexes = new Set();
    for (let i = 0; i < desired; i++) {
        indexes.add(Math.round(i * step));
    }
    return [...indexes];
}