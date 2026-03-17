let connectionObserver = null;

export function setConnectionObserver(observer) {
    connectionObserver = typeof observer === 'function' ? observer : null;
}

function notifyApiState(connected) {
    if (!connectionObserver) {
        return;
    }

    connectionObserver({
        kind: 'api',
        connected,
        at: new Date().toISOString(),
    });
}

async function requestRaw(url, options = {}) {
    try {
        const response = await fetch(url, options);
        notifyApiState(response.ok);
        return response;
    } catch (error) {
        notifyApiState(false);
        throw error;
    }
}

async function requestJson(url, options = {}) {
    const response = await requestRaw(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status} for ${url}`);
    }
    return await response.json();
}

export async function getDashboardData() {
    return await requestJson('/api/dashboard');
}

export async function getHistoryPage(limit = 20, offset = 0, rangeName = "all") {
    const query = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
        range_name: rangeName,
    });
    return await requestJson(`/api/history?${query.toString()}`);
}

export async function getSnapshotsPage(limit = 20, offset = 0) {
    const query = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
    });
    return await requestJson(`/api/snapshots?${query.toString()}`);
}

export async function getMetrics() {
    return await requestJson('/api/metrics');
}

export async function getRecentLogs(limit = 30) {
    const query = new URLSearchParams({ limit: String(limit) });
    return await requestJson(`/api/logs/recent?${query.toString()}`);
}

export async function postManualRecord(payload) {
    return await requestRaw('/api/manual-record', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}

export async function postToggleWarehouses(enabled) {
    return await requestRaw(`/api/settings/include-warehouses/${enabled ? 1 : 0}`, {
        method: "POST" 
    });
}

export async function postManualWarehouseValue(payload) {
    return await requestRaw('/api/manual-warehouse-value', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}