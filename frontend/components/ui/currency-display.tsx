import clsx from "clsx";
import { formatPkr } from "@/lib/format";

export function CurrencyDisplay({ amount, className }: { amount: string | number | null | undefined; className?: string }) {
  return <span className={clsx("tabular-nums", className)}>{formatPkr(amount)}</span>;
}