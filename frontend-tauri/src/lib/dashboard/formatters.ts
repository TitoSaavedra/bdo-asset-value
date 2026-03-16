export function money(value: number | null | undefined): string {
  const amount = Number(value || 0);
  const silverSymbol = "ⓢ";

  if (Math.abs(amount) >= 1_000_000_000_000) {
    const trillions = amount / 1_000_000_000_000;
    const formatted = new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(trillions);
    return `${silverSymbol} ${formatted}T`;
  }

  if (Math.abs(amount) >= 1_000_000_000) {
    const billions = amount / 1_000_000_000;
    const formatted = new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(billions);
    return `${silverSymbol} ${formatted}B`;
  }

  if (Math.abs(amount) >= 1_000_000) {
    const millions = amount / 1_000_000;
    const formatted = new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(millions);
    return `${silverSymbol} ${formatted}M`;
  }

  const formatted = new Intl.NumberFormat("es-CL", {
    maximumFractionDigits: 0,
  }).format(amount);

  return `${silverSymbol} ${formatted}`;
}

export function dateTime(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return date.toLocaleString("es-CL", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function shortDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return date.toLocaleDateString("es-CL", {
    day: "2-digit",
    month: "2-digit",
  });
}

export function compact(value: number | null | undefined): string {
  const amount = Number(value || 0);
  const absAmount = Math.abs(amount);

  if (absAmount >= 1_000_000_000_000) {
    return `${new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(amount / 1_000_000_000_000)}T`;
  }

  if (absAmount >= 1_000_000_000) {
    return `${new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(amount / 1_000_000_000)}B`;
  }

  if (absAmount >= 1_000_000) {
    return `${new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(amount / 1_000_000)}M`;
  }

  if (absAmount >= 1_000) {
    return `${new Intl.NumberFormat("es-CL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(amount / 1_000)}K`;
  }

  return new Intl.NumberFormat("es-CL", {
    maximumFractionDigits: 0,
  }).format(amount);
}
