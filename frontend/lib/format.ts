const KARACHI_TZ = "Asia/Karachi";

export function formatPkr(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number.parseFloat(value);
  if (Number.isNaN(num)) return String(value);
  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.includes("T") ? iso : `${iso}T12:00:00`);
  return new Intl.DateTimeFormat("en-PK", {
    timeZone: KARACHI_TZ,
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(d);
}

export const AGING_BUCKET_LABELS: Record<string, string> = {
  CURRENT: "Not Yet Due",
  "1_30": "1–30 Days Overdue",
  "31_60": "31–60 Days Overdue",
  "61_90": "61–90 Days Overdue",
  "91_PLUS": "More Than 90 Days Overdue",
};

export function agingBucketLabel(key: string): string {
  return AGING_BUCKET_LABELS[key] ?? key.replace(/_/g, " ");
}

export function overdueStatus(daysOverdue: number | null | undefined): string {
  if (daysOverdue === null || daysOverdue === undefined) return "—";
  if (daysOverdue <= 0) return "Not yet due";
  return `Overdue by ${daysOverdue} day${daysOverdue === 1 ? "" : "s"}`;
}