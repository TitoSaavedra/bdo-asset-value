export async function getDashboardData() {
    const response = await fetch("/api/dashboard");
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