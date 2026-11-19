import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" };

export function Button({ className, variant = "primary", ...props }: Props) {
  return (
    <button
      className={clsx(
        "inline-flex h-10 items-center justify-center rounded-lg px-4 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variant === "primary" && "bg-accent text-white hover:bg-accentHover",
        variant === "secondary" && "border border-border bg-surface text-ink hover:bg-canvas",
        variant === "ghost" && "text-muted hover:bg-canvas hover:text-ink",
        className,
      )}
      {...props}
    />
  );
}