import { compact, money, shortDate } from './utils.js';

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
    const marketSeries = records.map(x => x.market_silver || 0);
    const inventorySeries = records.map(x => x.inventory_silver || 0);
    const preorderSeries = records.map(x => x.preorder_silver || 0);
    const warehousesSeries = records.map(x => x.warehouses_total || 0);

    const allValues = [...totalSeries, ...marketSeries, ...inventorySeries, ...preorderSeries, ...warehousesSeries];
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

    // Dibujar las 5 series (Total, Mercado, Inventario, Preorden, Almacenes)
    drawSeries(totalSeries, "rgba(217,180,111,1)", "rgba(217,180,111,.18)");
    drawSeries(marketSeries, "rgba(90,164,255,1)", "rgba(90,164,255,.15)");
    drawSeries(inventorySeries, "rgba(243,221,176,1)", "rgba(243,221,176,.16)");
    drawSeries(preorderSeries, "rgba(97,211,145,1)", "rgba(97,211,145,.15)");
    drawSeries(warehousesSeries, "rgba(255,109,109,1)", "rgba(255,109,109,.15)");

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

    canvas.__chartMeta = {
        padding,
        plotW,
        plotH,
        dpr,
        xStep,
        records,
        totalSeries,
        marketSeries,
        inventorySeries,
        preorderSeries,
        warehousesSeries,
        yMin,
        yRange,
        includeWarehouses: include,
    };

    ensureChartHoverInteraction(canvas, () => renderChart(canvas, records, settings));

    if (typeof canvas.__hoverIndex === "number") {
        drawHoverTooltip(ctx, canvas.__chartMeta, canvas.__hoverIndex);
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


function ensureChartHoverInteraction(canvas, rerender) {
    if (canvas.__hoverBound) {
        return;
    }

    const clearHover = () => {
        if (canvas.__hoverIndex !== null) {
            canvas.__hoverIndex = null;
            rerender();
        }
    };

    canvas.__hoverIndex = null;

    canvas.addEventListener("mouseleave", clearHover);
    canvas.addEventListener("mousemove", (event) => {
        const meta = canvas.__chartMeta;
        if (!meta || meta.records.length === 0) {
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const x = (event.clientX - rect.left) * (canvas.width / rect.width);
        const y = (event.clientY - rect.top) * (canvas.height / rect.height);

        const minX = meta.padding.left;
        const maxX = meta.padding.left + meta.plotW;
        const minY = meta.padding.top;
        const maxY = meta.padding.top + meta.plotH;

        if (x < minX || x > maxX || y < minY || y > maxY) {
            clearHover();
            return;
        }

        const hoverIndex = meta.xStep === 0
            ? 0
            : Math.max(0, Math.min(meta.records.length - 1, Math.round((x - minX) / meta.xStep)));

        if (canvas.__hoverIndex !== hoverIndex) {
            canvas.__hoverIndex = hoverIndex;
            rerender();
        }
    });

    canvas.__hoverBound = true;
}


function drawHoverTooltip(ctx, meta, index) {
    const {
        padding,
        plotH,
        dpr,
        xStep,
        records,
        totalSeries,
        marketSeries,
        inventorySeries,
        preorderSeries,
        warehousesSeries,
        yMin,
        yRange,
        includeWarehouses,
    } = meta;

    if (index < 0 || index >= records.length) {
        return;
    }

    const x = padding.left + xStep * index;
    const pointY = (value) => padding.top + plotH - ((value - yMin) / yRange) * plotH;

    const totalY = pointY(totalSeries[index]);
    const marketY = pointY(marketSeries[index]);
    const inventoryY = pointY(inventorySeries[index]);
    const preorderY = pointY(preorderSeries[index]);
    const warehousesY = pointY(warehousesSeries[index]);

    ctx.save();

    // Vertical guide line
    ctx.strokeStyle = "rgba(243,221,176,0.45)";
    ctx.lineWidth = 1 * dpr;
    ctx.beginPath();
    ctx.moveTo(x, padding.top);
    ctx.lineTo(x, padding.top + plotH);
    ctx.stroke();

    // Hover points
    drawHoverPoint(ctx, x, totalY, "rgba(217,180,111,1)", dpr);
    drawHoverPoint(ctx, x, marketY, "rgba(90,164,255,1)", dpr);
    drawHoverPoint(ctx, x, inventoryY, "rgba(243,221,176,1)", dpr);
    drawHoverPoint(ctx, x, preorderY, "rgba(97,211,145,1)", dpr);
    drawHoverPoint(ctx, x, warehousesY, "rgba(255,109,109,1)", dpr);

    const lines = [
        `Fecha: ${records[index].captured_at}`,
        `Total (${includeWarehouses ? "c/alm" : "s/alm"}): ${money(totalSeries[index])}`,
        `Mercado: ${money(marketSeries[index])}`,
        `Inventario: ${money(inventorySeries[index])}`,
        `Preorden: ${money(preorderSeries[index])}`,
        `Almacenes: ${money(warehousesSeries[index])}`,
    ];

    ctx.font = `${12 * dpr}px Inter, Segoe UI, Arial`;
    const lineHeight = 18 * dpr;
    const textPadding = 10 * dpr;
    const tooltipWidth = Math.max(...lines.map((line) => ctx.measureText(line).width)) + textPadding * 2;
    const tooltipHeight = lines.length * lineHeight + textPadding * 2;

    let tooltipX = x + 14 * dpr;
    let tooltipY = padding.top + 12 * dpr;

    const maxTooltipX = meta.padding.left + meta.plotW - tooltipWidth;
    if (tooltipX > maxTooltipX) {
        tooltipX = x - tooltipWidth - 14 * dpr;
    }
    if (tooltipX < meta.padding.left) {
        tooltipX = meta.padding.left;
    }

    drawRoundedRect(ctx, tooltipX, tooltipY, tooltipWidth, tooltipHeight, 10 * dpr);
    ctx.fillStyle = "rgba(23,18,13,0.96)";
    ctx.fill();
    ctx.strokeStyle = "rgba(200,169,106,0.4)";
    ctx.lineWidth = 1 * dpr;
    ctx.stroke();

    ctx.fillStyle = "rgba(246,236,214,0.95)";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    lines.forEach((line, lineIndex) => {
        ctx.fillText(line, tooltipX + textPadding, tooltipY + textPadding + lineIndex * lineHeight);
    });

    ctx.restore();
}


function drawHoverPoint(ctx, x, y, color, dpr) {
    ctx.beginPath();
    ctx.fillStyle = color;
    ctx.arc(x, y, 4 * dpr, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.fillStyle = "rgba(9,8,6,0.96)";
    ctx.arc(x, y, 2 * dpr, 0, Math.PI * 2);
    ctx.fill();
}


function drawRoundedRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
}