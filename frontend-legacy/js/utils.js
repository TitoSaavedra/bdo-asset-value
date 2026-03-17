export function money(value) {
    const amount = Number(value || 0);
    const silverSymbol = "ⓢ";

    if (Math.abs(amount) >= 1_000_000_000_000) {
        const trillions = amount / 1_000_000_000_000;
        const formattedTrillions = new Intl.NumberFormat("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        }).format(trillions);
        return `${silverSymbol} ${formattedTrillions}T`;
    }

    if (Math.abs(amount) >= 1_000_000_000) {
        const billions = amount / 1_000_000_000;
        const formattedBillions = new Intl.NumberFormat("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        }).format(billions);
        return `${silverSymbol} ${formattedBillions}B`;
    }

    if (Math.abs(amount) >= 1_000_000) {
        const millions = amount / 1_000_000;
        const formattedMillions = new Intl.NumberFormat("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        }).format(millions);
        return `${silverSymbol} ${formattedMillions}M`;
    }

    const formattedAmount = new Intl.NumberFormat("es-CL", {
        maximumFractionDigits: 0,
    }).format(amount);

    return `${silverSymbol} ${formattedAmount}`;
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
    const amount = Number(value || 0);
    const absoluteAmount = Math.abs(amount);

    if (absoluteAmount >= 1_000_000_000_000) {
        const trillions = amount / 1_000_000_000_000;
        return `${new Intl.NumberFormat("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        }).format(trillions)}T`;
    }

    if (absoluteAmount >= 1_000_000_000) {
        const billions = amount / 1_000_000_000;
        return `${new Intl.NumberFormat("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        }).format(billions)}B`;
    }

    if (absoluteAmount >= 1_000_000) {
        const millions = amount / 1_000_000;
        return `${new Intl.NumberFormat("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        }).format(millions)}M`;
    }

    if (absoluteAmount >= 1_000) {
        const thousands = amount / 1_000;
        return `${new Intl.NumberFormat("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        }).format(thousands)}K`;
    }

    return new Intl.NumberFormat("es-CL", {
        maximumFractionDigits: 0,
    }).format(amount);
}