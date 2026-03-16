import type {
  DashboardPayload,
  LogItem,
  LogsPayload,
  MetricsPayload,
  PagedResponse,
  RecordItem,
  WarehouseSnapshot,
} from "./types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl(): string {
  return (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? DEFAULT_API_BASE_URL;
}

export function getWsUrl(): string {
  const explicit = import.meta.env.VITE_WS_URL as string | undefined;
  if (explicit) {
    return explicit;
  }

  return getApiBaseUrl().replace("http://", "ws://").replace("https://", "wss://") + "/ws/updates";
}

export async function requestRaw(
  path: string,
  updateApiConnection: (connected: boolean) => void,
  init: RequestInit = {},
): Promise<Response> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, init);
  updateApiConnection(response.ok);
  return response;
}

export async function requestJson<T>(
  path: string,
  updateApiConnection: (connected: boolean) => void,
  init: RequestInit = {},
): Promise<T> {
  const response = await requestRaw(path, updateApiConnection, init);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} en ${path}`);
  }

  return (await response.json()) as T;
}

export function fetchDashboard(updateApiConnection: (connected: boolean) => void): Promise<DashboardPayload> {
  return requestJson<DashboardPayload>("/api/dashboard?history_limit=80&snapshots_limit=250", updateApiConnection);
}

export function fetchHistoryPage(
  updateApiConnection: (connected: boolean) => void,
  limit: number,
  offset: number,
  rangeName: string,
): Promise<PagedResponse<RecordItem>> {
  return requestJson<PagedResponse<RecordItem>>(
    `/api/history?limit=${limit}&offset=${offset}&range_name=${rangeName}`,
    updateApiConnection,
  );
}

export function fetchSnapshotsPage(
  updateApiConnection: (connected: boolean) => void,
  limit: number,
  offset: number,
): Promise<PagedResponse<WarehouseSnapshot>> {
  return requestJson<PagedResponse<WarehouseSnapshot>>(
    `/api/snapshots?limit=${limit}&offset=${offset}`,
    updateApiConnection,
  );
}

export function fetchMetrics(updateApiConnection: (connected: boolean) => void): Promise<MetricsPayload> {
  return requestJson<MetricsPayload>("/api/metrics", updateApiConnection);
}

export async function fetchLogs(updateApiConnection: (connected: boolean) => void, limit = 30): Promise<LogItem[]> {
  const payload = await requestJson<LogsPayload>(`/api/logs/recent?limit=${limit}`, updateApiConnection);
  return payload.items;
}

export function postIncludeWarehouses(
  updateApiConnection: (connected: boolean) => void,
  enabled: boolean,
): Promise<unknown> {
  return requestJson(`/api/settings/include-warehouses/${enabled ? 1 : 0}`, updateApiConnection, { method: "POST" });
}

export function postManualRecord(
  updateApiConnection: (connected: boolean) => void,
  payload: {
    market_silver: number | null;
    inventory_silver: number | null;
    preorder_silver: number;
  },
): Promise<unknown> {
  return requestJson("/api/manual-record", updateApiConnection, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function postManualWarehouseValue(
  updateApiConnection: (connected: boolean) => void,
  payload: {
    warehouse: string;
    market_silver: number;
  },
): Promise<unknown> {
  return requestJson("/api/manual-warehouse-value", updateApiConnection, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
