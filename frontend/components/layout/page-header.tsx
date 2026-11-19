import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  disclaimer,
  meta,
}: {
  title: string;
  subtitle?: string;
  disclaimer?: string;
  meta?: ReactNode;
}) {
  return (
    <header className="mb-6 flex flex-col gap-4 border-b border-border pb-6 md:mb-8 md:flex-row md:items-start md:justify-between">
      <div className="min-w-0 flex-1">
        <h1 className="text-[1.75rem] font-semibold leading-tight tracking-tight text-ink md:text-[2rem]">
          {title}
        </h1>
        {subtitle ? <p className="mt-2 max-w-2xl text-sm text-muted">{subtitle}</p> : null}
        {disclaimer ? (
          <p className="mt-2 text-xs text-muted">{disclaimer}</p>
        ) : null}
      </div>
      {meta ? <div className="shrink-0 text-sm text-muted md:text-right">{meta}</div> : null}
    </header>
  );
}