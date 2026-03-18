<script lang="ts">
  import { onMount } from "svelte";
  import "$lib/styles/main.css";
  import AppSidebar from "$lib/components/dashboard/AppSidebar.svelte";
  import DashboardScreen from "$lib/components/dashboard/DashboardScreen.svelte";
  import ManualScreen from "$lib/components/dashboard/ManualScreen.svelte";
  import MetricsScreen from "$lib/components/dashboard/MetricsScreen.svelte";
  import WarehousesScreen from "$lib/components/dashboard/WarehousesScreen.svelte";
  import {
    fetchDashboard,
    fetchHistoryPage,
    fetchLogs,
    fetchMetrics,
    fetchSnapshotsPage,
    getWsUrl,
    postIncludeWarehouses,
    postManualRecord,
    postManualWarehouseValue,
  } from "$lib/dashboard/api";
  import { money } from "$lib/dashboard/formatters";
  import { renderChart } from "$lib/dashboard/chart";
  import {
    ALLOWED_THEMES,
    DEFAULT_VISIBLE_SERIES,
    type ChartRange,
    type DashboardPayload,
    type LogItem,
    type MetricsPayload,
    type PagedResponse,
    type RecordItem,
    type ScreenName,
    type ThemeName,
    type VisibleSeries,
    type WarehouseSnapshot,
    type DashboardComparisons,
  } from "$lib/dashboard/types";

  const CHART_PREFS_KEY = "bdo_asset_chart_prefs";
  const THEME_PREFS_KEY = "bdo_asset_theme";
  const DENSITY_PREFS_KEY = "bdo_asset_density";
  const TABLE_PAGE_SIZE = 20;
  const TOAST_LIFETIME_MS = 3200;

  type DensityMode = "normal" | "compact";

  type ToastTone = "ok" | "error" | "info";
  type ToastItem = {
    id: number;
    title: string;
    message: string;
    tone: ToastTone;
    leaving?: boolean;
  };

  let activeScreen = $state<ScreenName>("dashboard");
  let isLoading = $state(true);
  let errorMessage = $state("");
  let statusMessage = $state("");
  let toastItems = $state<ToastItem[]>([]);

  let dashboard = $state<DashboardPayload | null>(null);
  let historyPageData = $state<PagedResponse<RecordItem> | null>(null);
  let snapshotsPageData = $state<PagedResponse<WarehouseSnapshot> | null>(null);
  let metrics = $state<MetricsPayload | null>(null);
  let recentLogs = $state<LogItem[]>([]);

  let historyRange = $state<ChartRange>("all");
  let chartRange = $state<ChartRange>("all");
  let chartRecords = $state<RecordItem[]>([]);
  let visibleSeries = $state<VisibleSeries>({ ...DEFAULT_VISIBLE_SERIES });

  let historyPage = $state(1);
  let snapshotsPage = $state(1);
  let savingWarehouse = $state<string | null>(null);
  let lastSavedInlineWarehouse = $state<string | null>(null);
  let lastSavedInlineAt = $state(0);

  let theme = $state<ThemeName>("desert");
  let density = $state<DensityMode>("normal");
  let apiConnected = $state(false);
  let wsConnected = $state(false);
  let connectionUpdatedAt = $state<string | null>(null);

  let manualMarket = $state<number | null>(null);
  let manualInventory = $state<number | null>(null);
  let manualPreorder = $state<number>(0);
  let manualWarehouse = $state("");
  let manualWarehouseValue = $state<number | null>(null);

  let chartCanvas = $state<HTMLCanvasElement | null>(null);
  let wsRef: WebSocket | null = null;
  let resizeObserver: ResizeObserver | null = null;
  let nextToastId = 1;
  let hasLoadedInitialData = false;

  function pushToast(title: string, message: string, tone: ToastTone = "info"): void {
    const toastId = nextToastId++;
    toastItems = [...toastItems, { id: toastId, title, message, tone }];

    window.setTimeout(() => {
      toastItems = toastItems.map((item) => (item.id === toastId ? { ...item, leaving: true } : item));
      window.setTimeout(() => {
        toastItems = toastItems.filter((item) => item.id !== toastId);
      }, 220);
    }, TOAST_LIFETIME_MS);
  }

  function detectIncomingChanges(
    previousDashboard: DashboardPayload | null,
    previousSnapshots: PagedResponse<WarehouseSnapshot> | null,
    currentDashboard: DashboardPayload | null,
    currentSnapshots: PagedResponse<WarehouseSnapshot> | null,
  ): void {
    if (!hasLoadedInitialData) {
      hasLoadedInitialData = true;
      return;
    }

    const previousLatestAt = previousDashboard?.latest?.captured_at ?? null;
    const currentLatestAt = currentDashboard?.latest?.captured_at ?? null;
    if (currentLatestAt && currentLatestAt !== previousLatestAt) {
      pushToast("Nuevo registro", "Se actualizo el valor general de activos.", "info");
    }

    const previousSnapshotAt = previousSnapshots?.items?.[0]?.captured_at ?? null;
    const currentSnapshotAt = currentSnapshots?.items?.[0]?.captured_at ?? null;
    if (currentSnapshotAt && currentSnapshotAt !== previousSnapshotAt) {
      const warehouseName = currentSnapshots?.items?.[0]?.warehouse ?? "almacen";
      pushToast("Nuevo snapshot OCR", `Se registro un nuevo snapshot para ${warehouseName}.`, "info");
    }
  }

  function getLatestComparableValue(
    latestCapturedAt: string | null | undefined,
    selector: (record: RecordItem) => number | null | undefined,
  ): number | null {
    const records = dashboard?.records || [];
    for (let index = records.length - 1; index >= 0; index -= 1) {
      const record = records[index];
      if (!record || (latestCapturedAt && record.captured_at === latestCapturedAt)) {
        continue;
      }

      const value = selector(record);
      if (value !== null && value !== undefined) {
        return Number(value);
      }
    }

    return null;
  }

  function getDashboardComparisons(): DashboardComparisons {
    const latestRecord = dashboard?.latest;
    const latestCapturedAt = latestRecord?.captured_at;
    const includeWarehouses = Boolean(dashboard?.settings.include_warehouses_in_total);

    return {
      market: getLatestComparableValue(latestCapturedAt, (record) => record.market_silver),
      inventory: getLatestComparableValue(latestCapturedAt, (record) => record.inventory_silver),
      preorder: getLatestComparableValue(latestCapturedAt, (record) => record.preorder_silver),
      total: getLatestComparableValue(latestCapturedAt, (record) =>
        includeWarehouses ? record.total_with_warehouses : record.total_without_warehouses,
      ),
    };
  }

  function setConnection(kind: "api" | "ws", connected: boolean): void {
    if (kind === "api") {
      apiConnected = connected;
    } else {
      wsConnected = connected;
    }
    connectionUpdatedAt = new Date().toISOString();
  }

  function updateApiConnection(connected: boolean): void {
    setConnection("api", connected);
  }

  function formatConnectionTime(value: string | null): string {
    if (!value) {
      return "Sin actividad reciente";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return "Sin actividad reciente";
    }
    return `Última señal: ${parsed.toLocaleTimeString("es-CL")}`;
  }

  function applyTheme(nextTheme: string): void {
    const safeTheme = ALLOWED_THEMES.includes(nextTheme as ThemeName) ? (nextTheme as ThemeName) : "desert";
    theme = safeTheme;
    document.body.dataset.theme = safeTheme;
    localStorage.setItem(THEME_PREFS_KEY, safeTheme);
    renderChartView();
  }

  function previewTheme(nextTheme: string | null): void {
    const safeTheme = nextTheme && ALLOWED_THEMES.includes(nextTheme as ThemeName) ? (nextTheme as ThemeName) : theme;
    document.body.dataset.theme = safeTheme;
    renderChartView();
  }

  function loadThemePreference(): void {
    const savedTheme = localStorage.getItem(THEME_PREFS_KEY);
    applyTheme(savedTheme || "desert");
  }

  function applyDensity(nextDensity: string): void {
    const safeDensity: DensityMode = nextDensity === "compact" ? "compact" : "normal";
    density = safeDensity;
    document.body.dataset.density = safeDensity;
    localStorage.setItem(DENSITY_PREFS_KEY, safeDensity);
    renderChartView();
  }

  function loadDensityPreference(): void {
    const savedDensity = localStorage.getItem(DENSITY_PREFS_KEY);
    applyDensity(savedDensity || "normal");
  }

  function loadChartPreferences(): void {
    try {
      const raw = localStorage.getItem(CHART_PREFS_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as { chartRange?: ChartRange; visibleSeries?: VisibleSeries };
      chartRange = parsed.chartRange || "all";
      visibleSeries = { ...DEFAULT_VISIBLE_SERIES, ...(parsed.visibleSeries || {}) };
    } catch {
      chartRange = "all";
      visibleSeries = { ...DEFAULT_VISIBLE_SERIES };
    }
  }

  function saveChartPreferences(): void {
    localStorage.setItem(
      CHART_PREFS_KEY,
      JSON.stringify({
        chartRange,
        visibleSeries,
      }),
    );
  }

  function delta(current: number | null | undefined, previous: number | null | undefined): string {
    if (previous === null || previous === undefined) {
      return "Sin referencia";
    }

    const diff = Number(current || 0) - Number(previous || 0);
    if (diff === 0) {
      return "Sin cambio";
    }
    const direction = diff > 0 ? "▲" : "▼";
    return `${direction} ${money(diff)}`;
  }

  function deltaClass(current: number | null | undefined, previous: number | null | undefined): string {
    if (previous === null || previous === undefined) {
      return "delta-neutral";
    }

    const diff = Number(current || 0) - Number(previous || 0);
    if (diff > 0) {
      return "delta-up";
    }
    if (diff < 0) {
      return "delta-down";
    }
    return "delta-neutral";
  }

  async function refreshDashboard(): Promise<void> {
    dashboard = await fetchDashboard(updateApiConnection);
  }

  async function refreshHistoryPage(): Promise<void> {
    const offset = (historyPage - 1) * TABLE_PAGE_SIZE;
    historyPageData = await fetchHistoryPage(updateApiConnection, TABLE_PAGE_SIZE, offset, historyRange);
  }

  async function refreshSnapshotsPage(): Promise<void> {
    const offset = (snapshotsPage - 1) * TABLE_PAGE_SIZE;
    snapshotsPageData = await fetchSnapshotsPage(updateApiConnection, TABLE_PAGE_SIZE, offset);
  }

  async function refreshChartRecords(): Promise<void> {
    const page = await fetchHistoryPage(updateApiConnection, 220, 0, chartRange);
    chartRecords = [...page.items].reverse();
    renderChartView();
  }

  async function refreshMetricsAndLogs(): Promise<void> {
    const [metricsResponse, logsResponse] = await Promise.all([
      fetchMetrics(updateApiConnection),
      fetchLogs(updateApiConnection, 30),
    ]);
    metrics = metricsResponse;
    recentLogs = logsResponse;
  }

  async function refreshAll(options: { showLoading?: boolean } = {}): Promise<void> {
    const { showLoading = true } = options;
    if (showLoading) {
      isLoading = true;
    }
    errorMessage = "";
    const previousDashboard = dashboard;
    const previousSnapshots = snapshotsPageData;
    try {
      await Promise.all([
        refreshDashboard(),
        refreshHistoryPage(),
        refreshSnapshotsPage(),
        refreshChartRecords(),
        refreshMetricsAndLogs(),
      ]);
      detectIncomingChanges(previousDashboard, previousSnapshots, dashboard, snapshotsPageData);
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "No se pudo cargar la aplicación";
      setConnection("api", false);
    } finally {
      if (showLoading) {
        isLoading = false;
      }
    }
  }

  function renderChartView(): void {
    if (!chartCanvas || !dashboard) {
      return;
    }
    renderChart(chartCanvas, chartRecords, dashboard.settings, visibleSeries);
  }

  function connectWebSocket(): void {
    if (wsRef) {
      wsRef.close();
      wsRef = null;
    }

    wsRef = new WebSocket(getWsUrl());

    wsRef.onopen = () => {
      setConnection("ws", true);
      wsRef?.send("hello");
    };

    wsRef.onmessage = async () => {
      await refreshAll({ showLoading: false });
    };

    wsRef.onerror = () => {
      setConnection("ws", false);
    };

    wsRef.onclose = () => {
      setConnection("ws", false);
      window.setTimeout(connectWebSocket, 1600);
    };
  }

  async function changeHistoryRange(nextRange: ChartRange): Promise<void> {
    historyRange = nextRange;
    historyPage = 1;
    await refreshHistoryPage();
  }

  async function changeChartRange(nextRange: ChartRange): Promise<void> {
    chartRange = nextRange;
    saveChartPreferences();
    await refreshChartRecords();
  }

  async function setHistoryPage(nextPage: number): Promise<void> {
    if (!historyPageData) {
      return;
    }
    const totalPages = Math.max(1, Math.ceil(historyPageData.total / historyPageData.limit));
    historyPage = Math.max(1, Math.min(totalPages, nextPage));
    await refreshHistoryPage();
  }

  async function setSnapshotsPage(nextPage: number): Promise<void> {
    if (!snapshotsPageData) {
      return;
    }
    const totalPages = Math.max(1, Math.ceil(snapshotsPageData.total / snapshotsPageData.limit));
    snapshotsPage = Math.max(1, Math.min(totalPages, nextPage));
    await refreshSnapshotsPage();
  }

  function toggleSeries(seriesKey: keyof VisibleSeries): void {
    visibleSeries = {
      ...visibleSeries,
      [seriesKey]: !visibleSeries[seriesKey],
    };
    saveChartPreferences();
    renderChartView();
  }

  async function toggleIncludeWarehouses(enabled: boolean): Promise<void> {
    try {
      await postIncludeWarehouses(updateApiConnection, enabled);
      await Promise.all([refreshDashboard(), refreshChartRecords(), refreshHistoryPage()]);
      statusMessage = "Configuración actualizada";
      pushToast("Configuracion actualizada", enabled ? "Ahora el total incluye almacenes." : "Ahora el total excluye almacenes.", "ok");
    } catch (error) {
      statusMessage = "No se pudo actualizar la configuración";
      errorMessage = error instanceof Error ? error.message : "Error inesperado";
      pushToast("Error", "No se pudo actualizar la configuracion.", "error");
    }
  }

  async function saveManualRecordData(): Promise<void> {
    try {
      statusMessage = "Guardando registro manual...";
      await postManualRecord(updateApiConnection, {
        market_silver: manualMarket,
        inventory_silver: manualInventory,
        preorder_silver: manualPreorder,
      });
      statusMessage = "Registro manual guardado";
      await Promise.all([refreshDashboard(), refreshHistoryPage(), refreshChartRecords()]);
      pushToast("Registro guardado", "Se agrego un nuevo registro manual.", "ok");
    } catch (error) {
      statusMessage = "No se pudo guardar manual";
      errorMessage = error instanceof Error ? error.message : "Error inesperado";
      pushToast("Error", "No se pudo guardar el registro manual.", "error");
    }
  }

  async function saveManualWarehouseData(): Promise<void> {
    if (!manualWarehouse.trim() || manualWarehouseValue === null) {
      statusMessage = "Debes ingresar almacén y valor";
      return;
    }

    const warehouseName = manualWarehouse.trim();

    try {
      statusMessage = "Guardando almacén...";
      await postManualWarehouseValue(updateApiConnection, {
        warehouse: warehouseName,
        market_silver: manualWarehouseValue,
      });
      manualWarehouse = "";
      manualWarehouseValue = null;
      statusMessage = "Almacén guardado";
      await Promise.all([refreshDashboard(), refreshSnapshotsPage(), refreshChartRecords()]);
      pushToast("Almacen guardado", `Se guardo el valor manual para ${warehouseName}.`, "ok");
    } catch (error) {
      statusMessage = "No se pudo guardar almacén";
      errorMessage = error instanceof Error ? error.message : "Error inesperado";
      pushToast("Error", "No se pudo guardar el valor del almacen.", "error");
    }
  }

  async function saveWarehouseValue(warehouse: string, marketSilver: number): Promise<void> {
    if (!warehouse.trim()) {
      return;
    }

    if (!Number.isFinite(marketSilver) || marketSilver < 0) {
      return;
    }

    try {
      savingWarehouse = warehouse;
      statusMessage = `Guardando valor manual para ${warehouse}...`;
      await postManualWarehouseValue(updateApiConnection, {
        warehouse: warehouse.trim(),
        market_silver: Math.trunc(marketSilver),
      });
      statusMessage = `Valor manual guardado para ${warehouse}`;
      lastSavedInlineWarehouse = warehouse;
      lastSavedInlineAt = Date.now();
      await Promise.all([refreshDashboard(), refreshSnapshotsPage(), refreshChartRecords(), refreshHistoryPage()]);
      pushToast("Cambio aplicado", `Se actualizo el valor de ${warehouse}.`, "ok");
    } catch (error) {
      statusMessage = `No se pudo guardar valor para ${warehouse}`;
      errorMessage = error instanceof Error ? error.message : "Error inesperado";
      pushToast("Error", `No se pudo guardar el valor de ${warehouse}.`, "error");
    } finally {
      savingWarehouse = null;
    }
  }

  onMount(() => {
    loadThemePreference();
    loadDensityPreference();
    loadChartPreferences();
    void refreshAll();
    connectWebSocket();

    return () => {
      resizeObserver?.disconnect();
      wsRef?.close();
    };
  });

  $effect(() => {
    if (!chartCanvas) {
      return;
    }

    resizeObserver?.disconnect();
    resizeObserver = new ResizeObserver(() => renderChartView());
    resizeObserver.observe(chartCanvas);

    return () => {
      resizeObserver?.disconnect();
    };
  });

  $effect(() => {
    renderChartView();
  });
</script>

<div class="app">
  <AppSidebar
    {activeScreen}
    {theme}
    {density}
    {apiConnected}
    {wsConnected}
    {connectionUpdatedAt}
    onScreenChange={(screen) => (activeScreen = screen)}
    onThemeChange={applyTheme}
    onThemePreview={previewTheme}
    onDensityChange={applyDensity}
    onRefresh={refreshAll}
    {formatConnectionTime}
  />

  <main class="content">
    {#if isLoading}
      <section class="card panel state-panel">
        <h2 class="state-title">Cargando aplicación...</h2>
        <p class="state-description">Preparando dashboard, historial y métricas en tiempo real.</p>
      </section>
    {:else if errorMessage}
      <section class="card panel state-panel state-error">
        <h2 class="state-title">Error de carga</h2>
        <p class="state-description">{errorMessage}</p>
      </section>
    {/if}

    {#if activeScreen === "dashboard" && dashboard}
      <DashboardScreen
        {dashboard}
        comparisons={getDashboardComparisons()}
        {chartRange}
        {visibleSeries}
        {historyRange}
        {historyPage}
        {historyPageData}
        {savingWarehouse}
        {lastSavedInlineWarehouse}
        {lastSavedInlineAt}
        bind:chartCanvas
        onToggleIncludeWarehouses={toggleIncludeWarehouses}
        onChartRangeChange={changeChartRange}
        onSeriesToggle={toggleSeries}
        onSaveWarehouseValue={saveWarehouseValue}
        onHistoryRangeChange={changeHistoryRange}
        onHistoryPageChange={setHistoryPage}
        {delta}
        {deltaClass}
      />
    {:else if activeScreen === "dashboard" && !isLoading && !errorMessage}
      <section class="card panel state-panel">
        <h2 class="state-title">Sin datos para mostrar</h2>
        <p class="state-description">No se encontraron datos del dashboard todavía.</p>
      </section>
    {/if}

    {#if activeScreen === "manual"}
      <ManualScreen
        bind:manualMarket
        bind:manualInventory
        bind:manualPreorder
        bind:manualWarehouse
        bind:manualWarehouseValue
        {statusMessage}
        onSaveManualRecord={saveManualRecordData}
        onRefreshDashboard={refreshDashboard}
        onSaveManualWarehouse={saveManualWarehouseData}
      />
    {/if}

    {#if activeScreen === "warehouses" && dashboard}
      <WarehousesScreen
        {dashboard}
        {snapshotsPage}
        {snapshotsPageData}
        {savingWarehouse}
        {lastSavedInlineWarehouse}
        {lastSavedInlineAt}
        onSnapshotsPageChange={setSnapshotsPage}
        onSaveWarehouseValue={saveWarehouseValue}
      />
    {:else if activeScreen === "warehouses" && !isLoading && !errorMessage}
      <section class="card panel state-panel">
        <h2 class="state-title">Sin datos de almacenes</h2>
        <p class="state-description">Aún no hay estado de almacenes para renderizar.</p>
      </section>
    {/if}

    {#if activeScreen === "metrics" && metrics}
      <MetricsScreen {metrics} {recentLogs} onRefresh={refreshMetricsAndLogs} />
    {:else if activeScreen === "metrics" && !isLoading && !errorMessage}
      <section class="card panel state-panel">
        <h2 class="state-title">Sin métricas disponibles</h2>
        <p class="state-description">Las métricas se mostrarán cuando el backend publique datos.</p>
      </section>
    {/if}
  </main>
</div>

<div class="toast-region" aria-live="polite" aria-atomic="true">
  {#each toastItems as toast (toast.id)}
    <section class={`toast toast-${toast.tone} ${toast.leaving ? "toast-out" : ""}`}>
      <div class="toast-title">{toast.title}</div>
      <div class="toast-message">{toast.message}</div>
    </section>
  {/each}
</div>
