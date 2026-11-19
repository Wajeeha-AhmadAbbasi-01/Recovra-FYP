"use client";

import { agingBucketLabel } from "@/lib/format";

const ORDER = ["CURRENT", "1_30", "31_60", "61_90", "91_PLUS"] as const;

const SEGMENT_CLASS: Record<string, string> = {
  CURRENT: "bg-slate-300",
  "1_30": "bg-amber-400",
  "31_60": "bg-amber-500",
  "61_90": "bg-orange-500",
  "91_PLUS": "bg-danger",
};

export function AgingDistributionBar({
  buckets,
}: {
  buckets: Record<string, string>;
}) {
  const values = ORDER.map((k) => {
    const n = Number.parseFloat(buckets[k] ?? "0");
    return Number.isNaN(n) ? 0 : n;
  });
  const total = values.reduce((a, b) => a + b, 0);
  if (total <= 0) {
    return <p className="text-sm text-muted">No outstanding amounts to display.</p>;
  }

  return (
    <div className="space-y-3">
      <div
        className="flex h-2.5 w-full overflow-hidden rounded-full bg-border"
        role="img"
        aria-label="Distribution of outstanding amounts by aging bucket"
      >
        {ORDER.map((key, i) => {
          const pct = (values[i] / total) * 100;
          if (pct <= 0) return null;
          return (
            <span
              key={key}
              className={SEGMENT_CLASS[key]}
              style={{ width: `${pct}%` }}
              title={`${agingBucketLabel(key)}: ${pct.toFixed(1)}%`}
            />
          );
        })}
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        {ORDER.map((key, i) => (
          <li key={key} className="flex items-center gap-1.5">
            <span className={`inline-block h-2 w-2 rounded-sm ${SEGMENT_CLASS[key]}`} aria-hidden />
            <span>{agingBucketLabel(key)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}