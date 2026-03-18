<script lang="ts">
  import PaginationControls from "$lib/components/dashboard/PaginationControls.svelte";
  import { dateTime, money } from "$lib/dashboard/formatters";
  import type { DashboardPayload, PagedResponse, WarehouseSnapshot, WarehouseStatusItem } from "$lib/dashboard/types";

  let draftWarehouseValues = $state<Record<string, string>>({});
  let editingWarehouse = $state<string | null>(null);
  let editingValue = $state("");
  let highlightedWarehouse = $state<string | null>(null);
  let highlightTimeout: ReturnType<typeof window.setTimeout> | null = null;

  let {
    dashboard,
    snapshotsPage,
    snapshotsPageData,
    savingWarehouse,
    lastSavedInlineWarehouse,
    lastSavedInlineAt,
    onSnapshotsPageChange,
    onSaveWarehouseValue,
  }: {
    dashboard: DashboardPayload;
    snapshotsPage: number;
    snapshotsPageData: PagedResponse<WarehouseSnapshot> | null;
    savingWarehouse: string | null;
    lastSavedInlineWarehouse: string | null;
    lastSavedInlineAt: number;
    onSnapshotsPageChange: (page: number) => void | Promise<void>;
    onSaveWarehouseValue: (warehouse: string, marketSilver: number) => void | Promise<void>;
  } = $props();

  $effect(() => {
    const nextValues: Record<string, string> = {};
    for (const rowItem of dashboard.warehouse_status_list) {
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

  async function saveWarehouseRow(warehouse: string): Promise<void> {
    const parsed = Number(draftWarehouseValues[warehouse]);
    if (!Number.isFinite(parsed) || parsed < 0) {
      return;
    }
    await onSaveWarehouseValue(warehouse, Math.trunc(parsed));
  }

  function beginInlineEdit(rowItem: WarehouseStatusItem): void {
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

  async function commitInlineEdit(rowItem: WarehouseStatusItem): Promise<void> {
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
      await saveWarehouseRow(rowItem.warehouse);
    }

    cancelInlineEdit();
  }

  function getWarehouseAgeHours(lastCapturedAt: string | null): number | null {
    if (!lastCapturedAt) {
      return null;
    }

    const capturedAtMs = new Date(lastCapturedAt).getTime();
    if (!Number.isFinite(capturedAtMs)) {
      return null;
    }

    const ageHours = (Date.now() - capturedAtMs) / (1000 * 60 * 60);
    if (!Number.isFinite(ageHours)) {
      return null;
    }

    return Math.max(0, ageHours);
  }

  function getWarehouseStatusClass(lastCapturedAt: string | null): string {
    const ageHours = getWarehouseAgeHours(lastCapturedAt);
    if (ageHours === null) {
      return "status-stale";
    }

    if (ageHours < 5) {
      return "status-updated";
    }

    if (ageHours < 10) {
      return "status-review";
    }

    return "status-stale";
  }

  function getWarehouseStatusLabel(lastCapturedAt: string | null): string {
    const ageHours = getWarehouseAgeHours(lastCapturedAt);
    if (ageHours === null) {
      return "Desactualizado";
    }

    if (ageHours < 10) {
      return "Actualizado";
    }

    return "Desactualizado";
  }
</script>

<section class="warehouses-layout">
  <div class="card header">
    <h1>Activos por almacén</h1>
    <p>Estado y snapshots por almacén.</p>
  </div>

  <section class="card panel warehouses-panel">
    <div class="panel-head">
      <div>
        <h2>Listado actual por almacén</h2>
        <p class="section-subtitle">Estado más reciente y edición inline por almacén.</p>
      </div>
    </div>
    <p id="warehouseMissingInfo" class="sub">
      {dashboard.missing_warehouses.length ? `Faltan datos para: ${dashboard.missing_warehouses.join(", ")}` : "Todos los almacenes conocidos tienen datos."}
    </p>
    <div class="table-wrap table-scroll-y" id="warehouseStatusTableWrap">
      <table>
        <thead>
          <tr>
            <th>Almacén</th>
            <th>Valor actual</th>
            <th>Última actualización</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {#if !dashboard.warehouse_status_list.length}
            <tr><td colspan="4" class="empty-table-cell">Sin estado de almacenes.</td></tr>
          {:else}
            {#each dashboard.warehouse_status_list as rowItem}
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
                <td>{dateTime(rowItem.last_captured_at)}</td>
                <td>
                  <span class={`connection-pill ${getWarehouseStatusClass(rowItem.last_captured_at)}`}>
                    {getWarehouseStatusLabel(rowItem.last_captured_at)}
                  </span>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </section>

  <section class="card panel warehouses-panel">
    <div class="panel-head">
      <div>
        <h2>Snapshots OCR</h2>
        <p class="section-subtitle">Historial de capturas detectadas por OCR.</p>
      </div>
    </div>
    <div class="table-wrap table-scroll-y" id="warehouseSnapshotsTableWrap">
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Almacén</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          {#if !snapshotsPageData?.items.length}
            <tr><td colspan="3" class="empty-table-cell">Sin snapshots OCR aún.</td></tr>
          {:else}
            {#each snapshotsPageData?.items || [] as rowItem}
              <tr>
                <td>{dateTime(rowItem.captured_at)}</td>
                <td>{rowItem.warehouse}</td>
                <td>{money(rowItem.market_silver)}</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>

    {#if snapshotsPageData}
      <PaginationControls
        currentPage={snapshotsPage}
        totalItems={snapshotsPageData.total}
        pageSize={snapshotsPageData.limit}
        onPageChange={onSnapshotsPageChange}
      />
    {/if}
  </section>
</section>
