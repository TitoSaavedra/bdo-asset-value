export async function getDashboardData() {
    const response = await fetch("/api/dashboard");
    return await response.json();
}

export async function getHistoryPage(limit = 20, offset = 0, rangeName = "all") {
    const query = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
        range_name: rangeName,
    });
    const response = await fetch(`/api/history?${query.toString()}`);
    return await response.json();
}

export async function getSnapshotsPage(limit = 20, offset = 0) {
    const query = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
    });
    const response = await fetch(`/api/snapshots?${query.toString()}`);
    return await response.json();
}

export async function getMetrics() {
    const response = await fetch('/api/metrics');
    return await response.json();
}

export async function postManualRecord(payload) {
    return await fetch("/api/manual-record", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}

export async function postToggleWarehouses(enabled) {
    return await fetch(`/api/settings/include-warehouses/${enabled ? 1 : 0}`, { 
        method: "POST" 
    });
}

export async function postManualWarehouseValue(payload) {
    return await fetch("/api/manual-warehouse-value", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}