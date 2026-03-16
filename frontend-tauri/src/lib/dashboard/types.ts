export type ChartRange = "all" | "today" | "7d" | "30d";
export type ScreenName = "dashboard" | "manual" | "warehouses" | "metrics";

export type ThemeName = "desert" | "midnight" | "light";

export type RecordItem = {
  captured_at: string;
  market_silver: number | null;
  inventory_silver: number | null;
  preorder_silver: number;
  warehouses_total: number;
  total_with_warehouses: number;
  total_without_warehouses: number;
  source: string;
  details?: Record<string, unknown>;
};

export type WarehouseStatusItem = {
  warehouse: string;
  market_silver: number | null;
  last_captured_at: string | null;
  updated: boolean;
};

export type WarehouseSnapshot = {
  captured_at: string;
  warehouse: string;
  market_silver: number;
};

export type DashboardPayload = {
  latest: RecordItem | null;
  records: RecordItem[];
  warehouse_list: { warehouse: string; market_silver: number }[];
  warehouse_snapshots: WarehouseSnapshot[];
  warehouse_status_list: WarehouseStatusItem[];
  missing_warehouses: string[];
  settings: {
    include_warehouses_in_total: boolean;
  };
};

export type DashboardComparisons = {
  market: number | null;
  inventory: number | null;
  preorder: number | null;
  total: number | null;
};

export type PagedResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type MetricsPayload = {
  dashboard_render_ms_last: number;
  dashboard_render_ms_avg: number;
  dashboard_payload_bytes_last: number;
  dashboard_calls: number;
  writes_total: number;
  writes_per_minute: number;
};

export type LogItem = {
  timestamp: string;
  action_type: string;
  source: string;
  details: Record<string, unknown>;
};

export type LogsPayload = {
  items: LogItem[];
  total: number;
  limit: number;
};

export const ALLOWED_THEMES: ThemeName[] = ["desert", "midnight", "light"];

export const DEFAULT_VISIBLE_SERIES = {
  total: true,
  market: true,
  inventory: true,
  preorder: true,
  warehouses: true,
};

export type VisibleSeries = typeof DEFAULT_VISIBLE_SERIES;
