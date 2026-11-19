import clsx from "clsx";

export function LoadingSkeleton({ className }: { className?: string }) {
  return <div className={clsx("animate-pulse rounded-xl bg-accentSoft", className)} aria-hidden />;
}