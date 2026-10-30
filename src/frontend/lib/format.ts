const LOCALE = "en-GB";

export function viewerTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

function toDate(utc: string | Date): Date | null {
  const date = utc instanceof Date ? utc : new Date(utc);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateTime(
  utc: string | Date,
  timeZone: string = viewerTimeZone(),
): string {
  const date = toDate(utc);
  if (!date) return "—";
  return new Intl.DateTimeFormat(LOCALE, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
    timeZoneName: "short",
  }).format(date);
}

export function formatDate(
  utc: string | Date,
  timeZone: string = viewerTimeZone(),
): string {
  const date = toDate(utc);
  if (!date) return "—";
  return new Intl.DateTimeFormat(LOCALE, {
    dateStyle: "medium",
    timeZone,
  }).format(date);
}
