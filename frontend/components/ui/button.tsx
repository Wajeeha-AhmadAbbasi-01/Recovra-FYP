import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" };

export function Button({ className, variant = "primary", ...props }: Props) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:opacity-50",
        variant === "primary" && "bg-accent text-surface hover:opacity-90",
        variant === "secondary" && "bg-accentSoft text-ink border border-black/5",
        variant === "ghost" && "text-muted hover:text-ink",
        className,
      )}
      {...props}
    />
  );
}