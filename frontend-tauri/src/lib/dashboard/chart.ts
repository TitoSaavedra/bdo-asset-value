import { compact, money, shortDate } from "./formatters";
import type { RecordItem, VisibleSeries } from "./types";

type ChartSettings = {
  include_warehouses_in_total: boolean;
};

function chartColorVariables() {
  const rootStyles = getComputedStyle(document.body);
  const getColor = (name: string, fallback: string) => rootStyles.getPropertyValue(name).trim() || fallback;

  return {
    emptyText: getColor("--chart-empty-text", "rgba(246,236,214,0.72)"),
    grid: getColor("--chart-grid", "rgba(200,169,106,.16)"),
    axisText: getColor("--chart-axis-text", "rgba(185,171,141,.9)"),
    guideline: getColor("--chart-guideline", "rgba(243,221,176,0.45)"),
    tooltipBg: getColor("--chart-tooltip-bg", "rgba(23,18,13,0.96)"),
    tooltipBorder: getColor("--chart-tooltip-border", "rgba(200,169,106,0.4)"),
    tooltipText: getColor("--chart-tooltip-text", "rgba(246,236,214,0.95)"),
    hoverInnerDot: getColor("--chart-hover-inner-dot", "rgba(9,8,6,0.96)"),
    totalStroke: getColor("--chart-total-stroke", "rgba(217,180,111,1)"),
    totalFill: getColor("--chart-total-fill", "rgba(217,180,111,.18)"),
    marketStroke: getColor("--chart-market-stroke", "rgba(90,164,255,1)"),
    marketFill: getColor("--chart-market-fill", "rgba(90,164,255,.15)"),
    inventoryStroke: getColor("--chart-inventory-stroke", "rgba(243,221,176,1)"),
    inventoryFill: getColor("--chart-inventory-fill", "rgba(243,221,176,.16)"),
    preorderStroke: getColor("--chart-preorder-stroke", "rgba(97,211,145,1)"),
    preorderFill: getColor("--chart-preorder-fill", "rgba(97,211,145,.15)"),
    warehousesStroke: getColor("--chart-warehouses-stroke", "rgba(255,109,109,1)"),
    warehousesFill: getColor("--chart-warehouses-fill", "rgba(255,109,109,.15)"),
  };
}

function computeLabelIndexes(length: number): number[] {
  if (length <= 6) {
    return Array.from({ length }, (_, i) => i);
  }

  const desired = 6;
  const step = (length - 1) / (desired - 1);
  const indexes = new Set<number>();
  for (let i = 0; i < desired; i += 1) {
    indexes.add(Math.round(i * step));
  }

  return [...indexes];
}

function drawRoundedRect(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number): void {
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

function drawHoverPoint(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  color: string,
  innerDotColor: string,
  dpr: number,
): void {
  ctx.beginPath();
  ctx.fillStyle = color;
  ctx.arc(x, y, 4 * dpr, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.fillStyle = innerDotColor;
  ctx.arc(x, y, 2 * dpr, 0, Math.PI * 2);
  ctx.fill();
}

function bindChartHover(canvas: HTMLCanvasElement, rerender: () => void): void {
  if (canvas.dataset.hoverBound === "1") {
    return;
  }

  canvas.addEventListener("mouseleave", () => {
    canvas.dataset.hoverIndex = "";
    rerender();
  });

  canvas.addEventListener("mousemove", (event) => {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const dpr = window.devicePixelRatio || 1;
    const scaledX = x * dpr;
    const scaledY = y * dpr;

    const padding = {
      top: 30 * dpr,
      right: 20 * dpr,
      bottom: 44 * dpr,
      left: 82 * dpr,
    };

    const plotW = canvas.width - padding.left - padding.right;
    const plotH = canvas.height - padding.top - padding.bottom;

    const minX = padding.left;
    const maxX = padding.left + plotW;
    const minY = padding.top;
    const maxY = padding.top + plotH;

    if (scaledX < minX || scaledX > maxX || scaledY < minY || scaledY > maxY) {
      canvas.dataset.hoverIndex = "";
      rerender();
      return;
    }

    const pointsCount = Number(canvas.dataset.pointsCount || 0);
    const xStep = pointsCount <= 1 ? 0 : plotW / (pointsCount - 1);
    const nextHoverIndex = xStep === 0 ? 0 : Math.max(0, Math.min(pointsCount - 1, Math.round((scaledX - minX) / xStep)));

    if (canvas.dataset.hoverIndex !== String(nextHoverIndex)) {
      canvas.dataset.hoverIndex = String(nextHoverIndex);
      rerender();
    }
  });

  canvas.dataset.hoverBound = "1";
}

export function renderChart(
  canvas: HTMLCanvasElement,
  records: RecordItem[],
  settings: ChartSettings,
  visibleSeries: VisibleSeries,
): void {
  const contextOrNull = canvas.getContext("2d");
  if (!contextOrNull) {
    return;
  }

  const context: CanvasRenderingContext2D = contextOrNull;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(320, Math.floor(rect.width * dpr));
  const height = Math.max(280, Math.floor(rect.height * dpr));

  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }

  context.clearRect(0, 0, canvas.width, canvas.height);
  const colors = chartColorVariables();

  if (!records.length) {
    context.fillStyle = colors.emptyText;
    context.font = `${16 * dpr}px Inter, Segoe UI, Arial`;
    context.textAlign = "center";
    context.fillText("Sin datos para graficar", canvas.width / 2, canvas.height / 2);
    return;
  }

  const include = Boolean(settings.include_warehouses_in_total);
  const totalSeries = records.map((x) => (include ? x.total_with_warehouses : x.total_without_warehouses));
  const marketSeries = records.map((x) => x.market_silver || 0);
  const inventorySeries = records.map((x) => x.inventory_silver || 0);
  const preorderSeries = records.map((x) => x.preorder_silver || 0);
  const warehousesSeries = records.map((x) => x.warehouses_total || 0);

  const allValues: number[] = [];
  if (visibleSeries.total) allValues.push(...totalSeries);
  if (visibleSeries.market) allValues.push(...marketSeries);
  if (visibleSeries.inventory) allValues.push(...inventorySeries);
  if (visibleSeries.preorder) allValues.push(...preorderSeries);
  if (visibleSeries.warehouses) allValues.push(...warehousesSeries);

  if (!allValues.length) {
    context.fillStyle = colors.emptyText;
    context.font = `${16 * dpr}px Inter, Segoe UI, Arial`;
    context.textAlign = "center";
    context.fillText("Selecciona al menos una serie", canvas.width / 2, canvas.height / 2);
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

  context.strokeStyle = colors.grid;
  context.lineWidth = 1 * dpr;
  for (let i = 0; i <= 5; i += 1) {
    const y = padding.top + (plotH / 5) * i;
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(padding.left + plotW, y);
    context.stroke();
  }

  context.fillStyle = colors.axisText;
  context.font = `${12 * dpr}px Inter, Segoe UI, Arial`;
  context.textAlign = "right";
  context.textBaseline = "middle";
  for (let i = 0; i <= 5; i += 1) {
    const value = yMax - (yRange / 5) * i;
    const y = padding.top + (plotH / 5) * i;
    context.fillText(compact(value), padding.left - 10 * dpr, y);
  }

  function drawSeries(values: number[], strokeColor: string, fillColor: string): void {
    const step = values.length === 1 ? 0 : plotW / (values.length - 1);
    const points = values.map((value, index) => ({
      x: padding.left + step * index,
      y: padding.top + plotH - ((value - yMin) / yRange) * plotH,
    }));

    if (points.length === 1) {
      context.beginPath();
      context.fillStyle = strokeColor;
      context.arc(points[0].x, points[0].y, 4 * dpr, 0, Math.PI * 2);
      context.fill();
      return;
    }

    const gradient = context.createLinearGradient(0, padding.top, 0, padding.top + plotH);
    gradient.addColorStop(0, fillColor);
    gradient.addColorStop(1, "rgba(0,0,0,0)");

    context.beginPath();
    context.moveTo(points[0].x, padding.top + plotH);
    context.lineTo(points[0].x, points[0].y);

    for (let i = 1; i < points.length; i += 1) {
      const prev = points[i - 1];
      const curr = points[i];
      const cx = (prev.x + curr.x) / 2;
      context.quadraticCurveTo(prev.x, prev.y, cx, (prev.y + curr.y) / 2);
    }

    const last = points[points.length - 1];
    context.lineTo(last.x, last.y);
    context.lineTo(last.x, padding.top + plotH);
    context.closePath();
    context.fillStyle = gradient;
    context.fill();

    context.beginPath();
    context.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i += 1) {
      const prev = points[i - 1];
      const curr = points[i];
      const cx = (prev.x + curr.x) / 2;
      context.quadraticCurveTo(prev.x, prev.y, cx, (prev.y + curr.y) / 2);
    }
    context.lineTo(last.x, last.y);
    context.strokeStyle = strokeColor;
    context.lineWidth = 3 * dpr;
    context.stroke();
  }

  if (visibleSeries.total) drawSeries(totalSeries, colors.totalStroke, colors.totalFill);
  if (visibleSeries.market) drawSeries(marketSeries, colors.marketStroke, colors.marketFill);
  if (visibleSeries.inventory) drawSeries(inventorySeries, colors.inventoryStroke, colors.inventoryFill);
  if (visibleSeries.preorder) drawSeries(preorderSeries, colors.preorderStroke, colors.preorderFill);
  if (visibleSeries.warehouses) drawSeries(warehousesSeries, colors.warehousesStroke, colors.warehousesFill);

  const labelIndexes = computeLabelIndexes(records.length);
  context.textAlign = "center";
  context.textBaseline = "top";
  context.fillStyle = colors.axisText;
  context.font = `${11 * dpr}px Inter, Segoe UI, Arial`;

  const xStep = records.length === 1 ? 0 : plotW / (records.length - 1);
  for (const index of labelIndexes) {
    const x = padding.left + xStep * index;
    context.fillText(shortDate(records[index].captured_at), x, padding.top + plotH + 12 * dpr);
  }

  canvas.dataset.pointsCount = String(records.length);
  bindChartHover(canvas, () => renderChart(canvas, records, settings, visibleSeries));

  const hoverIndex = canvas.dataset.hoverIndex ? Number(canvas.dataset.hoverIndex) : null;
  if (hoverIndex === null || Number.isNaN(hoverIndex) || hoverIndex < 0 || hoverIndex >= records.length) {
    return;
  }

  const pointY = (value: number) => padding.top + plotH - ((value - yMin) / yRange) * plotH;
  const x = padding.left + xStep * hoverIndex;

  context.save();
  context.strokeStyle = colors.guideline;
  context.lineWidth = 1 * dpr;
  context.beginPath();
  context.moveTo(x, padding.top);
  context.lineTo(x, padding.top + plotH);
  context.stroke();

  if (visibleSeries.total) drawHoverPoint(context, x, pointY(totalSeries[hoverIndex]), colors.totalStroke, colors.hoverInnerDot, dpr);
  if (visibleSeries.market) drawHoverPoint(context, x, pointY(marketSeries[hoverIndex]), colors.marketStroke, colors.hoverInnerDot, dpr);
  if (visibleSeries.inventory) drawHoverPoint(context, x, pointY(inventorySeries[hoverIndex]), colors.inventoryStroke, colors.hoverInnerDot, dpr);
  if (visibleSeries.preorder) drawHoverPoint(context, x, pointY(preorderSeries[hoverIndex]), colors.preorderStroke, colors.hoverInnerDot, dpr);
  if (visibleSeries.warehouses) drawHoverPoint(context, x, pointY(warehousesSeries[hoverIndex]), colors.warehousesStroke, colors.hoverInnerDot, dpr);

  const lines = [`Fecha: ${records[hoverIndex].captured_at}`];
  if (visibleSeries.total) lines.push(`Total (${include ? "c/alm" : "s/alm"}): ${money(totalSeries[hoverIndex])}`);
  if (visibleSeries.market) lines.push(`Mercado: ${money(marketSeries[hoverIndex])}`);
  if (visibleSeries.inventory) lines.push(`Inventario: ${money(inventorySeries[hoverIndex])}`);
  if (visibleSeries.preorder) lines.push(`Preorden: ${money(preorderSeries[hoverIndex])}`);
  if (visibleSeries.warehouses) lines.push(`Almacenes: ${money(warehousesSeries[hoverIndex])}`);

  context.font = `${12 * dpr}px Inter, Segoe UI, Arial`;
  const lineHeight = 18 * dpr;
  const textPadding = 10 * dpr;
  const tooltipWidth = Math.max(...lines.map((line) => context.measureText(line).width)) + textPadding * 2;
  const tooltipHeight = lines.length * lineHeight + textPadding * 2;

  let tooltipX = x + 14 * dpr;
  const tooltipY = padding.top + 12 * dpr;
  const maxTooltipX = padding.left + plotW - tooltipWidth;

  if (tooltipX > maxTooltipX) {
    tooltipX = x - tooltipWidth - 14 * dpr;
  }
  if (tooltipX < padding.left) {
    tooltipX = padding.left;
  }

  drawRoundedRect(context, tooltipX, tooltipY, tooltipWidth, tooltipHeight, 10 * dpr);
  context.fillStyle = colors.tooltipBg;
  context.fill();
  context.strokeStyle = colors.tooltipBorder;
  context.lineWidth = 1 * dpr;
  context.stroke();

  context.fillStyle = colors.tooltipText;
  context.textAlign = "left";
  context.textBaseline = "top";
  lines.forEach((line, lineIndex) => {
    context.fillText(line, tooltipX + textPadding, tooltipY + textPadding + lineIndex * lineHeight);
  });

  context.restore();
}
