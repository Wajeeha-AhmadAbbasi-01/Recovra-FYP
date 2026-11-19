import { formatDate } from "@/lib/format";

export function DateDisplay({ iso, className }: { iso: string | null | undefined; className?: string }) {
  return <span className={className}>{formatDate(iso)}</span>;
}