export function fmtPct(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "-";
  return `${(100 * x).toFixed(digits)}%`;
}

export function fmtNum(x: number | null | undefined, digits = 3): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "-";
  return x.toFixed(digits);
}

export function fmtSigned(x: number | null | undefined, digits = 3): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "-";
  const sign = x > 0 ? "+" : "";
  return `${sign}${x.toFixed(digits)}`;
}

export function fmtMoney(x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "-";
  return `$${x.toFixed(digits)}`;
}

export function fmtMult(x: number | null | undefined, digits = 2): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "-";
  return `${x.toFixed(digits)}×`;
}
