<script lang="ts">
  import { compact, dateTime } from "$lib/dashboard/formatters";
  import type { LogItem, MetricsPayload } from "$lib/dashboard/types";

  function formatLogDetails(details: Record<string, unknown>): string {
    try {
      return JSON.stringify(details, null, 2);
    } catch {
      return String(details);
    }
  }

  let {
    metrics,
    recentLogs,
    onRefresh,
  }: {
    metrics: MetricsPayload | null;
    recentLogs: LogItem[];
    onRefresh: () => void | Promise<void>;
  } = $props();
</script>

<section class="metrics-layout">
  <div class="card header">
    <h1>Métricas</h1>
    <p>Rendimiento backend en tiempo real.</p>
  </div>

  <section class="card panel metrics-panel metrics-summary-panel">
    <div class="panel-head">
      <h2>Resumen de rendimiento</h2>
      <div class="toolbar">
        <button class="history-filter-btn" onclick={onRefresh}>Actualizar</button>
      </div>
    </div>

    <div class="grid-4 metrics-grid">
      <div class="card metric metrics-card">
        <div class="k">Dashboard (último)</div>
        <div class="v">{compact(metrics?.dashboard_render_ms_last)} ms</div>
        <div class="s">Tiempo de render del último cálculo</div>
      </div>
      <div class="card metric metrics-card">
        <div class="k">Dashboard (promedio)</div>
        <div class="v">{compact(metrics?.dashboard_render_ms_avg)} ms</div>
        <div class="s">Promedio de render acumulado</div>
      </div>
      <div class="card metric metrics-card">
        <div class="k">Payload último</div>
        <div class="v">{compact(metrics?.dashboard_payload_bytes_last)} B</div>
        <div class="s">Tamaño del dashboard serializado</div>
      </div>
      <div class="card metric metrics-card">
        <div class="k">Writes / min</div>
        <div class="v">{compact(metrics?.writes_per_minute)}</div>
        <div class="s">Escrituras recientes por minuto</div>
      </div>
    </div>

    <div class="table-wrap" id="metricsTableWrap">
      <table>
        <thead>
          <tr>
            <th>Métrica</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>dashboard_calls</td><td>{metrics?.dashboard_calls ?? 0}</td></tr>
          <tr><td>writes_total</td><td>{metrics?.writes_total ?? 0}</td></tr>
          <tr><td>dashboard_render_ms_last</td><td>{metrics?.dashboard_render_ms_last ?? 0}</td></tr>
          <tr><td>dashboard_render_ms_avg</td><td>{metrics?.dashboard_render_ms_avg ?? 0}</td></tr>
          <tr><td>dashboard_payload_bytes_last</td><td>{metrics?.dashboard_payload_bytes_last ?? 0}</td></tr>
          <tr><td>writes_per_minute</td><td>{metrics?.writes_per_minute ?? 0}</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <section class="card panel metrics-panel metrics-logs-panel">
    <div class="panel-head">
      <h2>Logs recientes</h2>
    </div>
    <div class="table-wrap table-scroll-y" id="recentLogsTableWrap">
      <table>
        <thead>
          <tr>
            <th>Hora</th>
            <th>Acción</th>
            <th>Origen</th>
            <th>Detalle</th>
          </tr>
        </thead>
        <tbody>
          {#if !recentLogs.length}
            <tr><td colspan="4" class="empty-table-cell">Sin acciones recientes.</td></tr>
          {:else}
            {#each recentLogs as rowItem}
              <tr>
                <td>{dateTime(rowItem.timestamp)}</td>
                <td>{rowItem.action_type}</td>
                <td>{rowItem.source}</td>
                <td class="log-details-cell"><pre class="log-details">{formatLogDetails(rowItem.details)}</pre></td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </section>
</section>
