<script lang="ts">
  let {
    manualMarket = $bindable<number | null>(),
    manualInventory = $bindable<number | null>(),
    manualPreorder = $bindable<number>(),
    manualWarehouse = $bindable<string>(),
    manualWarehouseValue = $bindable<number | null>(),
    statusMessage,
    onSaveManualRecord,
    onRefreshDashboard,
    onSaveManualWarehouse,
  }: {
    manualMarket: number | null;
    manualInventory: number | null;
    manualPreorder: number;
    manualWarehouse: string;
    manualWarehouseValue: number | null;
    statusMessage: string;
    onSaveManualRecord: () => void | Promise<void>;
    onRefreshDashboard: () => void | Promise<void>;
    onSaveManualWarehouse: () => void | Promise<void>;
  } = $props();
</script>

<div class="card header">
  <h1>Registro manual</h1>
  <p>Carga valores manuales.</p>
</div>

<section class="card panel">
  <div class="field-grid">
    <div class="field">
      <label for="marketInput">Silver mercado</label>
      <input id="marketInput" type="number" min="0" bind:value={manualMarket} placeholder="8508622614" />
    </div>
    <div class="field">
      <label for="inventoryInput">Silver inventario</label>
      <input id="inventoryInput" type="number" min="0" bind:value={manualInventory} placeholder="500000" />
    </div>
    <div class="field">
      <label for="preorderInput">Silver preorder</label>
      <input id="preorderInput" type="number" min="0" bind:value={manualPreorder} placeholder="0" />
    </div>
  </div>
  <div class="actions">
    <button class="btn btn-primary" onclick={onSaveManualRecord}>Guardar manual</button>
    <button class="btn btn-secondary" onclick={onRefreshDashboard}>Actualizar dashboard</button>
  </div>
</section>

<section class="card panel">
  <h2>Valor manual de almacén</h2>
  <div class="field-grid">
    <div class="field">
      <label for="warehouseInput">Almacén</label>
      <input id="warehouseInput" type="text" bind:value={manualWarehouse} placeholder="Velia" />
    </div>
    <div class="field">
      <label for="warehouseValueInput">Silver almacén</label>
      <input id="warehouseValueInput" type="number" min="0" bind:value={manualWarehouseValue} placeholder="1200000000" />
    </div>
  </div>
  <div class="actions">
    <button class="btn btn-primary" onclick={onSaveManualWarehouse}>Guardar almacén</button>
  </div>
</section>

{#if statusMessage}
  <section class="card panel">
    <p class="status">{statusMessage}</p>
  </section>
{/if}
