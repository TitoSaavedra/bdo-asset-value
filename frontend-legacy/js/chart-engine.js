import { compact, money, shortDate } from './utils.js';

function chartColorVariables() {
    const rootStyles = getComputedStyle(document.body);
    const getColor = (name, fallback) => rootStyles.getPropertyValue(name).trim() || fallback;

    return {
        emptyText: getColor('--chart-empty-text', 'rgba(246,236,214,0.72)'),
        grid: getColor('--chart-grid', 'rgba(200,169,106,.16)'),
        axisText: getColor('--chart-axis-text', 'rgba(185,171,141,.9)'),
        guideline: getColor('--chart-guideline', 'rgba(243,221,176,0.45)'),
        tooltipBg: getColor('--chart-tooltip-bg', 'rgba(23,18,13,0.96)'),
        tooltipBorder: getColor('--chart-tooltip-border', 'rgba(200,169,106,0.4)'),
        tooltipText: getColor('--chart-tooltip-text', 'rgba(246,236,214,0.95)'),
        hoverInnerDot: getColor('--chart-hover-inner-dot', 'rgba(9,8,6,0.96)'),
        totalStroke: getColor('--chart-total-stroke', 'rgba(217,180,111,1)'),
        totalFill: getColor('--chart-total-fill', 'rgba(217,180,111,.18)'),
        marketStroke: getColor('--chart-market-stroke', 'rgba(90,164,255,1)'),
        marketFill: getColor('--chart-market-fill', 'rgba(90,164,255,.15)'),
        inventoryStroke: getColor('--chart-inventory-stroke', 'rgba(243,221,176,1)'),
        inventoryFill: getColor('--chart-inventory-fill', 'rgba(243,221,176,.16)'),
        preorderStroke: getColor('--chart-preorder-stroke', 'rgba(97,211,145,1)'),
        preorderFill: getColor('--chart-preorder-fill', 'rgba(97,211,145,.15)'),
        warehousesStroke: getColor('--chart-warehouses-stroke', 'rgba(255,109,109,1)'),
        warehousesFill: getColor('--chart-warehouses-fill', 'rgba(255,109,109,.15)'),
    };
}

/**
 * Renderiza el gráfico de evolución de plata en el canvas.
 */
export function renderChart(canvas, records, settings, options = {}) {
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
    const colors = chartColorVariables();

    if (!records || records.length === 0) {
        ctx.fillStyle = colors.emptyText;
        ctx.font = `${16 * dpr}px Inter, Segoe UI, Arial`;
        ctx.textAlign = "center";
        ctx.fillText("Sin datos para graficar", canvas.width / 2, canvas.height / 2);
        return;
    }

    // --- Configuración de Escalas ---
    const include = !!settings.include_warehouses_in_total;
    const visibleSeries = {
        total: options.visibleSeries?.total !== false,
        market: options.visibleSeries?.market !== false,
        inventory: options.visibleSeries?.inventory !== false,
        preorder: options.visibleSeries?.preorder !== false,
        warehouses: options.visibleSeries?.warehouses !== false,
    };
    const totalSeries = records.map(x => include ? x.total_with_warehouses : x.total_without_warehouses);
    const marketSeries = records.map(x => x.market_silver || 0);
    const inventorySeries = records.map(x => x.inventory_silver || 0);
    const preorderSeries = records.map(x => x.preorder_silver || 0);
    const warehousesSeries = records.map(x => x.warehouses_total || 0);

    const allValues = [];
    if (visibleSeries.total) allValues.push(...totalSeries);
    if (visibleSeries.market) allValues.push(...marketSeries);
    if (visibleSeries.inventory) allValues.push(...inventorySeries);
    if (visibleSeries.preorder) allValues.push(...preorderSeries);
    if (visibleSeries.warehouses) allValues.push(...warehousesSeries);

    if (allValues.length === 0) {
        ctx.fillStyle = colors.emptyText;
        ctx.font = `${16 * dpr}px Inter, Segoe UI, Arial`;
        ctx.textAlign = "center";
        ctx.fillText("Selecciona al menos una serie", canvas.width / 2, canvas.height / 2);
        return;
    }

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
    ctx.strokeStyle = colors.grid;
    ctx.lineWidth = 1 * dpr;
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (plotH / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + plotW, y);
        ctx.stroke();
    }

    // --- Etiquetas Eje Y ---
    ctx.fillStyle = colors.axisText;
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

    // Dibujar las series visibles
    if (visibleSeries.total) drawSeries(totalSeries, colors.totalStroke, colors.totalFill);
    if (visibleSeries.market) drawSeries(marketSeries, colors.marketStroke, colors.marketFill);
    if (visibleSeries.inventory) drawSeries(inventorySeries, colors.inventoryStroke, colors.inventoryFill);
    if (visibleSeries.preorder) drawSeries(preorderSeries, colors.preorderStroke, colors.preorderFill);
    if (visibleSeries.warehouses) drawSeries(warehousesSeries, colors.warehousesStroke, colors.warehousesFill);

    // --- Etiquetas Eje X (Fechas) ---
    const labelIndexes = computeLabelIndexes(records.length);
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = colors.axisText;
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
        visibleSeries,
    };

    ensureChartHoverInteraction(canvas, () => renderChart(canvas, records, settings, options));

    if (typeof canvas.__hoverIndex === "number") {
        drawHoverTooltip(ctx, canvas.__chartMeta, canvas.__hoverIndex, colors);
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


function drawHoverTooltip(ctx, meta, index, colors) {
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
        visibleSeries,
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
    ctx.strokeStyle = colors.guideline;
    ctx.lineWidth = 1 * dpr;
    ctx.beginPath();
    ctx.moveTo(x, padding.top);
    ctx.lineTo(x, padding.top + plotH);
    ctx.stroke();

    // Hover points
    if (visibleSeries.total) drawHoverPoint(ctx, x, totalY, colors.totalStroke, colors.hoverInnerDot, dpr);
    if (visibleSeries.market) drawHoverPoint(ctx, x, marketY, colors.marketStroke, colors.hoverInnerDot, dpr);
    if (visibleSeries.inventory) drawHoverPoint(ctx, x, inventoryY, colors.inventoryStroke, colors.hoverInnerDot, dpr);
    if (visibleSeries.preorder) drawHoverPoint(ctx, x, preorderY, colors.preorderStroke, colors.hoverInnerDot, dpr);
    if (visibleSeries.warehouses) drawHoverPoint(ctx, x, warehousesY, colors.warehousesStroke, colors.hoverInnerDot, dpr);

    const lines = [`Fecha: ${records[index].captured_at}`];
    if (visibleSeries.total) lines.push(`Total (${includeWarehouses ? "c/alm" : "s/alm"}): ${money(totalSeries[index])}`);
    if (visibleSeries.market) lines.push(`Mercado: ${money(marketSeries[index])}`);
    if (visibleSeries.inventory) lines.push(`Inventario: ${money(inventorySeries[index])}`);
    if (visibleSeries.preorder) lines.push(`Preorden: ${money(preorderSeries[index])}`);
    if (visibleSeries.warehouses) lines.push(`Almacenes: ${money(warehousesSeries[index])}`);

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
    ctx.fillStyle = colors.tooltipBg;
    ctx.fill();
    ctx.strokeStyle = colors.tooltipBorder;
    ctx.lineWidth = 1 * dpr;
    ctx.stroke();

    ctx.fillStyle = colors.tooltipText;
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    lines.forEach((line, lineIndex) => {
        ctx.fillText(line, tooltipX + textPadding, tooltipY + textPadding + lineIndex * lineHeight);
    });

    ctx.restore();
}


function drawHoverPoint(ctx, x, y, color, innerDotColor, dpr) {
    ctx.beginPath();
    ctx.fillStyle = color;
    ctx.arc(x, y, 4 * dpr, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.fillStyle = innerDotColor;
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