"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { agingBucketLabel, formatDate, formatPkr } from "@/lib/format";
import { PageHeader } from "@/components/layout/page-header";
import { SectionPanel } from "@/components/layout/section-panel";
import { AgingDistributionBar } from "@/components/ui/aging-distribution-bar";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { DashboardStatCard } from "@/components/ui/dashboard-stat-card";
import { DataTable, DataTableBody, DataTableHead, DataTableRow, DataTableTd, DataTableTh } from "@/components/ui/data-table";
import { DateDisplay } from "@/components/ui/date-display";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";

const BUCKET_ORDER = ["CURRENT", "1_30", "31_60", "61_90", "91_PLUS"] as const;

export default function DashboardPage() {
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [aging, setAging] = useState<Record<string, string>>({});
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [overdue, setOverdue] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.dashboardSummary(), api.dashboardAging(), api.dashboardOverdue()])
      .then(([s, a, o]) => {
        if (s.error || a.error || o.error) {
          setError(s.error?.message ?? a.error?.message ?? o.error?.message ?? "Could not load dashboard");
          return;
        }
        setSummary(s.data ?? null);
        setAging(a.data?.buckets ?? {});
        setCounts(a.data?.bucket_counts ?? {});
        setOverdue(o.data ?? []);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton className="h-24 w-full" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-[120px]" />
          ))}
        </div>
      </div>
    );
  }

  if (error) return <ErrorState message={error} />;

  const asOf = summary?.as_of_date as string | undefined;
  const updatedLabel = asOf ? `Updated: ${formatDate(asOf)}` : undefined;

  return (
    <div className="space-y-6 md:space-y-8">
      <PageHeader
        title="Receivables Dashboard"
        subtitle="Your invoices, outstanding payments, and overdue balances at a glance."
        disclaimer="Figures are based on locally accepted invoices. This is not official FBR verification."
        meta={updatedLabel ? <span className="tabular-nums">{updatedLabel}</span> : null}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <DashboardStatCard
          label="Total Outstanding"
          value={<CurrencyDisplay amount={String(summary?.total_outstanding ?? "0")} />}
          icon={<IconWallet />}
        />
        <DashboardStatCard
          label="Total Unpaid Invoices"
          value={String(summary?.invoice_count ?? "0")}
          icon={<IconFile />}
        />
        <DashboardStatCard
          label="Overdue Amount"
          value={<CurrencyDisplay amount={String(summary?.overdue_amount ?? "0")} />}
          icon={<IconAlert />}
        />
        <DashboardStatCard
          label="Overdue Invoices"
          value={String(summary?.overdue_invoice_count ?? "0")}
          icon={<IconClock />}
        />
      </div>

      <SectionPanel
        title="Invoice Aging"
        description="Outstanding balance and invoice count by due-date bucket (Asia/Karachi)."
      >
        <AgingDistributionBar buckets={aging} />
        <ul className="mt-6 divide-y divide-border">
          {BUCKET_ORDER.map((key) => (
            <li key={key} className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0">
              <div>
                <p className="text-sm font-medium text-ink">{agingBucketLabel(key)}</p>
                <p className="text-xs text-muted">
                  {(counts[key] ?? 0) as number} invoice{(counts[key] ?? 0) === 1 ? "" : "s"}
                </p>
              </div>
              <p className="text-base font-semibold tabular-nums text-ink">{formatPkr(aging[key] ?? "0")}</p>
            </li>
          ))}
        </ul>
      </SectionPanel>

      <SectionPanel
        title="Invoices Requiring Attention"
        description="Customers with invoices past their payment due dates."
        action={
          <Link href="/invoices" className="text-sm font-medium no-underline hover:underline">
            View all invoices
          </Link>
        }
      >
        {!overdue.length ? (
          <EmptyState
            title="Great! There are no overdue invoices at the moment."
            action={
              <Link href="/invoices" className="text-sm font-medium">
                View all invoices
              </Link>
            }
          />
        ) : (
          <DataTable>
            <DataTableHead>
              <DataTableRow>
                <DataTableTh>Customer</DataTableTh>
                <DataTableTh>Invoice number</DataTableTh>
                <DataTableTh>Due date</DataTableTh>
                <DataTableTh align="right">Days overdue</DataTableTh>
                <DataTableTh align="right">Outstanding</DataTableTh>
                <DataTableTh>Status</DataTableTh>
                <DataTableTh>Action</DataTableTh>
              </DataTableRow>
            </DataTableHead>
            <DataTableBody>
              {overdue.map((row) => (
                <DataTableRow key={String(row.id)}>
                  <DataTableTd className="max-w-[180px] truncate font-medium">{String(row.customer_name)}</DataTableTd>
                  <DataTableTd className="font-mono text-xs">{String(row.invoice_reference)}</DataTableTd>
                  <DataTableTd>
                    <DateDisplay iso={row.due_date as string} />
                  </DataTableTd>
                  <DataTableTd align="right">{String(row.days_overdue)}</DataTableTd>
                  <DataTableTd align="right">
                    <CurrencyDisplay amount={String(row.outstanding_amount)} />
                  </DataTableTd>
                  <DataTableTd>
                    <StatusBadge status="Overdue" label="Overdue" />
                  </DataTableTd>
                  <DataTableTd>
                    <Link href={`/invoices/${row.id}`} className="text-sm font-medium no-underline hover:underline">
                      View invoice
                    </Link>
                  </DataTableTd>
                </DataTableRow>
              ))}
            </DataTableBody>
          </DataTable>
        )}
      </SectionPanel>
    </div>
  );
}

function IconWallet() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
      <path d="M4 8V6a2 2 0 012-2h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2v-2M20 12H8" />
    </svg>
  );
}
function IconFile() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
      <path d="M8 4h8l4 4v12H4V4h4z" />
    </svg>
  );
}
function IconAlert() {
  return (
    <svg className="h-5 w-5 text-warning" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
      <path d="M12 9v4m0 4h.01M10.3 4.6h3.4L21 19H3L10.3 4.6z" />
    </svg>
  );
}
function IconClock() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}