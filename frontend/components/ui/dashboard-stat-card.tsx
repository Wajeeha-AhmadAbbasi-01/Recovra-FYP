import clsx from "clsx";
import type { ReactNode } from "react";

export function DashboardStatCard({
  label,
  value,
  icon,
  subtitle,
  className,
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  subtitle?: string;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "flex min-h-[120px] flex-col justify-between rounded-card border border-border bg-surface p-5",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-[13px] font-medium leading-snug text-muted">{label}</p>
        {icon ? <div className="shrink-0 text-muted">{icon}</div> : null}
      </div>
      <div className="mt-3 min-w-0">
        <p className="break-words text-[clamp(1.25rem,2.5vw,1.75rem)] font-semibold leading-tight tabular-nums text-ink">
          {value}
        </p>
        {subtitle ? <p className="mt-1 text-xs text-muted">{subtitle}</p> : null}
      </div>
    </div>
  );
}