import clsx from "clsx";
import type { HTMLAttributes, ThHTMLAttributes } from "react";

export function DataTable({ className, children, ...props }: HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="-mx-1 overflow-x-auto">
      <table className={clsx("min-w-full border-collapse text-sm", className)} {...props}>
        {children}
      </table>
    </div>
  );
}

export function DataTableHead({ children }: { children: React.ReactNode }) {
  return <thead className="bg-tableHeader text-left">{children}</thead>;
}

export function DataTableBody({ children }: { children: React.ReactNode }) {
  return <tbody className="divide-y divide-border">{children}</tbody>;
}

export function DataTableRow({ className, children, ...props }: HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={clsx("transition-colors hover:bg-canvas/80", className)} {...props}>
      {children}
    </tr>
  );
}

export function DataTableTh({
  className,
  align = "left",
  children,
  ...props
}: ThHTMLAttributes<HTMLTableCellElement> & { align?: "left" | "right" }) {
  return (
    <th
      className={clsx(
        "px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted",
        align === "right" && "text-right",
        className,
      )}
      {...props}
    >
      {children}
    </th>
  );
}

export function DataTableTd({
  className,
  align = "left",
  children,
  ...props
}: HTMLAttributes<HTMLTableCellElement> & { align?: "left" | "right" }) {
  return (
    <td
      className={clsx(
        "whitespace-nowrap px-4 py-3.5 text-sm text-ink",
        align === "right" && "text-right tabular-nums",
        className,
      )}
      {...props}
    >
      {children}
    </td>
  );
}