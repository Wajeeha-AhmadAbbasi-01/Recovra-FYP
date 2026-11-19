import clsx from "clsx";
import type { ReactNode } from "react";

export function SectionPanel({
  title,
  description,
  action,
  children,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={clsx("rounded-card border border-border bg-surface", className)}>
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-5 py-4 md:px-6">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-ink">{title}</h2>
          {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
        </div>
        {action}
      </div>
      <div className="p-5 md:p-6">{children}</div>
    </section>
  );
}