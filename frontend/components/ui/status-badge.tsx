import clsx from "clsx";

const STYLES: Record<string, string> = {
  ACCEPTED_LOCAL_CHECK: "bg-success/10 text-success",
  REJECTED_LOCAL_CHECK: "bg-danger/10 text-danger",
  NEEDS_MANUAL_REVIEW: "bg-warning/10 text-warning",
  REJECTED_UNSUPPORTED: "bg-danger/10 text-danger",
  DUPLICATE: "bg-warning/10 text-warning",
  PROCESSING_ERROR: "bg-danger/10 text-danger",
};

export function StatusBadge({ status }: { status: string }) {
  const label = status.replace(/_/g, " ").toLowerCase();
  return (
    <span className={clsx("rounded-full px-2.5 py-1 text-xs font-medium capitalize", STYLES[status] ?? "bg-accentSoft text-muted")}>
      {label}
      <span className="sr-only"> — local check only, not FBR verified</span>
    </span>
  );
}