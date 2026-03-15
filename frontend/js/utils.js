export function money(value) {
    return new Intl.NumberFormat("es-CL", {
        style: "currency", currency: "CLP", maximumFractionDigits: 0,
    }).format(value || 0);
}

export function dateTime(value) {
    return new Date(value).toLocaleString("es-CL", {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
}

export function shortDate(value) {
    return new Date(value).toLocaleDateString("es-CL", {
        day: "2-digit", month: "2-digit",
    });
}

export function compact(value) {
    return new Intl.NumberFormat("es-CL", {
        notation: "compact", maximumFractionDigits: 1,
    }).format(value || 0);
}