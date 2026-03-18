<script lang="ts">
  import { money, dateTime } from "$lib/dashboard/formatters";
  import PaginationControls from "$lib/components/dashboard/PaginationControls.svelte";
  import type { ChartRange, DashboardComparisons, DashboardPayload, PagedResponse, RecordItem, VisibleSeries } from "$lib/dashboard/types";

  let draftWarehouseValues = $state<Record<string, string>>({});
  let editingWarehouse = $state<string | null>(null);
  let editingValue = $state("");
  let highlightedWarehouse = $state<string | null>(null);
  let highlightTimeout: ReturnType<typeof window.setTimeout> | null = null;

  let {
    dashboard,
    comparisons,
    chartRange,
    visibleSeries,
    historyRange,
    historyPage,
    historyPageData,
    savingWarehouse,
    lastSavedInlineWarehouse,
    lastSavedInlineAt,
    chartCanvas = $bindable<HTMLCanvasElement | null>(),
    onToggleIncludeWarehouses,
    onChartRangeChange,
    onSeriesToggle,
    onSaveWarehouseValue,
    onHistoryRangeChange,
    onHistoryPageChange,
    delta,
    deltaClass,
  }: {
    dashboard: DashboardPayload;
    comparisons: DashboardComparisons;
    chartRange: ChartRange;
    visibleSeries: VisibleSeries;
    historyRange: ChartRange;
    historyPage: number;
    historyPageData: PagedResponse<RecordItem> | null;
    savingWarehouse: string | null;
    lastSavedInlineWarehouse: string | null;
    lastSavedInlineAt: number;
    chartCanvas: HTMLCanvasElement | null;
    onToggleIncludeWarehouses: (enabled: boolean) => void | Promise<void>;
    onChartRangeChange: (range: ChartRange) => void | Promise<void>;
    onSeriesToggle: (key: keyof VisibleSeries) => void;
    onSaveWarehouseValue: (warehouse: string, marketSilver: number) => void | Promise<void>;
    onHistoryRangeChange: (range: ChartRange) => void | Promise<void>;
    onHistoryPageChange: (page: number) => void | Promise<void>;
    delta: (current: number | null | undefined, previous: number | null | undefined) => string;
    deltaClass: (current: number | null | undefined, previous: number | null | undefined) => string;
  } = $props();

  $effect(() => {
    const nextValues: Record<string, string> = {};
    for (const rowItem of dashboard.warehouse_list) {
      nextValues[rowItem.warehouse] = String(Math.trunc(Number(rowItem.market_silver || 0)));
    }
    draftWarehouseValues = nextValues;
  });

  $effect(() => {
    if (!lastSavedInlineWarehouse || !lastSavedInlineAt) {
      return;
    }

    highlightedWarehouse = lastSavedInlineWarehouse;
    if (highlightTimeout) {
      window.clearTimeout(highlightTimeout);
    }
    highlightTimeout = window.setTimeout(() => {
      highlightedWarehouse = null;
    }, 1500);
  });

  function beginInlineEdit(rowItem: { warehouse: string; market_silver: number }): void {
    if (savingWarehouse) {
      return;
    }

    const currentValue = Math.trunc(Number(draftWarehouseValues[rowItem.warehouse] ?? rowItem.market_silver ?? 0));
    editingWarehouse = rowItem.warehouse;
    editingValue = String(currentValue);
  }

  function cancelInlineEdit(): void {
    editingWarehouse = null;
    editingValue = "";
  }

  async function commitInlineEdit(rowItem: { warehouse: string; market_silver: number }): Promise<void> {
    if (editingWarehouse !== rowItem.warehouse) {
      return;
    }

    const parsed = Number(editingValue);
    if (!Number.isFinite(parsed) || parsed < 0) {
      cancelInlineEdit();
      return;
    }

    const nextValue = Math.trunc(parsed);
    const currentValue = Math.trunc(Number(rowItem.market_silver || 0));
    draftWarehouseValues = {
      ...draftWarehouseValues,
      [rowItem.warehouse]: String(nextValue),
    };

    if (nextValue !== currentValue) {
      await onSaveWarehouseValue(rowItem.warehouse, nextValue);
    }

    cancelInlineEdit();
  }

</script>

<div class="card header">
  <h1>Dashboard</h1>
  <p>Vista general de valor total, evolución y estado por origen.</p>
</div>

<div class="grid-4">
  <div class="card metric">
    <div class="k">Mercado</div>
    <div class="v">{money(dashboard.latest?.market_silver)}</div>
    <div class="s">Mercado actual</div>
    <div class={`metric-delta ${deltaClass(dashboard.latest?.market_silver, comparisons.market)}`}>
      {delta(dashboard.latest?.market_silver, comparisons.market)}
    </div>
  </div>
  <div class="card metric">
    <div class="k">Inventario</div>
    <div class="v">{money(dashboard.latest?.inventory_silver)}</div>
    <div class="s">Inventario actual</div>
    <div class={`metric-delta ${deltaClass(dashboard.latest?.inventory_silver, comparisons.inventory)}`}>
      {delta(dashboard.latest?.inventory_silver, comparisons.inventory)}
    </div>
  </div>
  <div class="card metric">
    <div class="k">Preorders</div>
    <div class="v">{money(dashboard.latest?.preorder_silver)}</div>
    <div class="s">Preorders actuales</div>
    <div class={`metric-delta ${deltaClass(dashboard.latest?.preorder_silver, comparisons.preorder)}`}>
      {delta(dashboard.latest?.preorder_silver, comparisons.preorder)}
    </div>
  </div>
  <div class="card metric">
    <div class="k">Total</div>
    <div class="v">{money(dashboard.settings.include_warehouses_in_total ? dashboard.latest?.total_with_warehouses : dashboard.latest?.total_without_warehouses)}</div>
    <div class="s">{dashboard.settings.include_warehouses_in_total ? "Incluye almacenes" : "No incluye almacenes"}</div>
    <div class={`metric-delta ${deltaClass(dashboard.settings.include_warehouses_in_total ? dashboard.latest?.total_with_warehouses : dashboard.latest?.total_without_warehouses, comparisons.total)}`}>
      {delta(dashboard.settings.include_warehouses_in_total ? dashboard.latest?.total_with_warehouses : dashboard.latest?.total_without_warehouses, comparisons.total)}
    </div>
  </div>
</div>

<div class="row">
  <section class="card panel">
    <div class="panel-head">
      <div>
        <h2>Evolución histórica</h2>
        <p class="section-subtitle">Tendencia consolidada y comparación por fuente de valor.</p>
      </div>
      <div class="toolbar chart-range-filters">
        <button class={`history-filter-btn ${chartRange === "all" ? "active" : ""}`} onclick={() => onChartRangeChange("all")}>Todo</button>
        <button class={`history-filter-btn ${chartRange === "today" ? "active" : ""}`} onclick={() => onChartRangeChange("today")}>Hoy</button>
        <button class={`history-filter-btn ${chartRange === "7d" ? "active" : ""}`} onclick={() => onChartRangeChange("7d")}>7 días</button>
        <button class={`history-filter-btn ${chartRange === "30d" ? "active" : ""}`} onclick={() => onChartRangeChange("30d")}>30 días</button>
      </div>
    </div>

    <label class="toggle-enhanced">
      <input
        type="checkbox"
        checked={dashboard.settings.include_warehouses_in_total}
        onchange={(event) => onToggleIncludeWarehouses((event.currentTarget as HTMLInputElement).checked)}
      />
      <span class="toggle-track">
        <span class="toggle-thumb"></span>
      </span>
      <span class="toggle-label">Sumar almacenes</span>
    </label>

    <canvas bind:this={chartCanvas} id="chart"></canvas>

    <div class="chart-legend" aria-label="Leyenda del gráfico">
      <button
        class={`legend-item ${visibleSeries.total ? "" : "legend-disabled"}`}
        type="button"
        aria-pressed={visibleSeries.total}
        onclick={() => onSeriesToggle("total")}
      ><span class="legend-dot legend-total"></span><span class="legend-text">Total</span></button>
      <button
        class={`legend-item ${visibleSeries.market ? "" : "legend-disabled"}`}
        type="button"
        aria-pressed={visibleSeries.market}
        onclick={() => onSeriesToggle("market")}
      ><span class="legend-dot legend-market"></span><span class="legend-text">Mercado</span></button>
      <button
        class={`legend-item ${visibleSeries.inventory ? "" : "legend-disabled"}`}
        type="button"
        aria-pressed={visibleSeries.inventory}
        onclick={() => onSeriesToggle("inventory")}
      ><span class="legend-dot legend-inventory"></span><span class="legend-text">Inventario</span></button>
      <button
        class={`legend-item ${visibleSeries.preorder ? "" : "legend-disabled"}`}
        type="button"
        aria-pressed={visibleSeries.preorder}
        onclick={() => onSeriesToggle("preorder")}
      ><span class="legend-dot legend-preorder"></span><span class="legend-text">Preorden</span></button>
      <button
        class={`legend-item ${visibleSeries.warehouses ? "" : "legend-disabled"}`}
        type="button"
        aria-pressed={visibleSeries.warehouses}
        onclick={() => onSeriesToggle("warehouses")}
      ><span class="legend-dot legend-warehouses"></span><span class="legend-text">Almacenes</span></button>
    </div>
  </section>

  <section class="card panel">
    <div class="panel-head">
      <div>
        <h2>Resumen almacenes</h2>
        <p class="section-subtitle">Edición rápida de valor actual por almacén.</p>
      </div>
    </div>
    <div class="table-wrap table-scroll-y">
      <table>
        <thead>
          <tr>
            <th>Almacén</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          {#if !dashboard.warehouse_list.length}
            <tr><td colspan="2" class="empty-table-cell">Sin datos de almacenes.</td></tr>
          {:else}
            {#each dashboard.warehouse_list as rowItem}
              <tr>
                <td>{rowItem.warehouse}</td>
                <td>
                  {#if editingWarehouse === rowItem.warehouse}
                    <input
                      class="inline-edit-input warehouse-inline-input"
                      type="number"
                      min="0"
                      step="1"
                      bind:value={editingValue}
                      onkeydown={async (event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          await commitInlineEdit(rowItem);
                        }

                        if (event.key === "Escape") {
                          event.preventDefault();
                          cancelInlineEdit();
                        }
                      }}
                      onblur={() => void commitInlineEdit(rowItem)}
                    />
                  {:else}
                    <button
                      class={`inline-edit-trigger ${highlightedWarehouse === rowItem.warehouse ? "inline-edit-saved" : ""}`}
                      type="button"
                      disabled={Boolean(savingWarehouse)}
                      onclick={() => beginInlineEdit(rowItem)}
                      title="Click para editar"
                    >{savingWarehouse === rowItem.warehouse ? "Guardando..." : money(rowItem.market_silver)}</button>
                  {/if}
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </section>
</div>

<section class="card panel">
  <div class="panel-head">
    <div>
      <h2>Historial general</h2>
      <p class="section-subtitle">Registros cronológicos para auditoría y seguimiento.</p>
    </div>
    <div class="toolbar history-filters">
      <button class={`history-filter-btn ${historyRange === "all" ? "active" : ""}`} onclick={() => onHistoryRangeChange("all")}>Todo</button>
      <button class={`history-filter-btn ${historyRange === "today" ? "active" : ""}`} onclick={() => onHistoryRangeChange("today")}>Hoy</button>
      <button class={`history-filter-btn ${historyRange === "7d" ? "active" : ""}`} onclick={() => onHistoryRangeChange("7d")}>7 días</button>
      <button class={`history-filter-btn ${historyRange === "30d" ? "active" : ""}`} onclick={() => onHistoryRangeChange("30d")}>30 días</button>
    </div>
  </div>

  <div class="table-wrap table-scroll-y">
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Fuente</th>
          <th>Mercado</th>
          <th>Inventario</th>
          <th>Preorder</th>
          <th>Total sin almacenes</th>
          <th>Total con almacenes</th>
        </tr>
      </thead>
      <tbody>
        {#if !historyPageData?.items.length}
          <tr><td colspan="7" class="empty-table-cell">Sin registros en el rango seleccionado.</td></tr>
        {:else}
          {#each historyPageData?.items || [] as rowItem}
            <tr>
              <td>{dateTime(rowItem.captured_at)}</td>
              <td>{rowItem.source}</td>
              <td>{money(rowItem.market_silver)}</td>
              <td>{money(rowItem.inventory_silver)}</td>
              <td>{money(rowItem.preorder_silver)}</td>
              <td>{money(rowItem.total_without_warehouses)}</td>
              <td>{money(rowItem.total_with_warehouses)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  {#if historyPageData}
    <PaginationControls
      currentPage={historyPage}
      totalItems={historyPageData.total}
      pageSize={historyPageData.limit}
      onPageChange={onHistoryPageChange}
    />
  {/if}
</section>
