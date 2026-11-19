import clsx from "clsx";

const STYLES: Record<string, string> = {
  ACCEPTED_LOCAL_CHECK: "bg-emerald-50 text-success ring-1 ring-emerald-100",
  REJECTED_LOCAL_CHECK: "bg-red-50 text-danger ring-1 ring-red-100",
  NEEDS_MANUAL_REVIEW: "bg-amber-50 text-warning ring-1 ring-amber-100",
  REJECTED_UNSUPPORTED: "bg-red-50 text-danger ring-1 ring-red-100",
  DUPLICATE: "bg-amber-50 text-warning ring-1 ring-amber-100",
  PROCESSING_ERROR: "bg-red-50 text-danger ring-1 ring-red-100",
  Overdue: "bg-red-50 text-danger ring-1 ring-red-100",
  "Not yet due": "bg-slate-50 text-muted ring-1 ring-border",
};

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const display = label ?? status.replace(/_/g, " ").toLowerCase();
  return (
    <span
      className={clsx(
        "inline-flex max-w-full items-center rounded-md px-2 py-0.5 text-xs font-medium capitalize",
        STYLES[status] ?? "bg-canvas text-muted ring-1 ring-border",
      )}
    >
      {display}
      <span className="sr-only"> — local check only, not FBR verified</span>
    </span>
  );
}