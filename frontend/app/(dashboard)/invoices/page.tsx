"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { agingBucketLabel, overdueStatus } from "@/lib/format";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { DateDisplay } from "@/components/ui/date-display";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { DataTable, DataTableBody, DataTableHead, DataTableRow, DataTableTd, DataTableTh } from "@/components/ui/data-table";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export default function InvoicesPage() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.invoices(q).then((res) => {
      if (res.error) {
        setError(res.error.message ?? "Could not load invoices");
        setLoading(false);
        return;
      }
      setRows(res.data ?? []);
      setLoading(false);
    });
  }, [q]);

  return (
    <div>
      <PageHeader
        title="Invoices"
        subtitle="Search and review accepted invoices in this workspace."
        disclaimer="Local format checks only — not FBR verification."
      />
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <Input
            placeholder="Search by invoice reference"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="max-w-sm"
            aria-label="Search invoices"
          />
          {q ? (
            <Button type="button" variant="secondary" onClick={() => setQ("")}>
              Clear search
            </Button>
          ) : null}
        </div>

        {error ? <div className="mt-4"><ErrorState message={error} /></div> : null}
        {loading ? <LoadingSkeleton className="mt-6 h-32" /> : null}

        {!loading && !error ? (
          <div className="mt-6">
            <DataTable>
              <DataTableHead>
                <DataTableRow>
                  <DataTableTh>Reference</DataTableTh>
                  <DataTableTh>Customer</DataTableTh>
                  <DataTableTh>Due date</DataTableTh>
                  <DataTableTh align="right">Outstanding</DataTableTh>
                  <DataTableTh>Aging</DataTableTh>
                  <DataTableTh>Status</DataTableTh>
                  <DataTableTh>Action</DataTableTh>
                </DataTableRow>
              </DataTableHead>
              <DataTableBody>
                {rows.map((inv) => {
                  const statusText = overdueStatus(inv.days_overdue as number | null);
                  return (
                    <DataTableRow key={String(inv.id)}>
                      <DataTableTd className="font-mono text-xs font-medium">{String(inv.invoice_reference)}</DataTableTd>
                      <DataTableTd className="max-w-[160px] truncate">{String(inv.customer_name ?? "—")}</DataTableTd>
                      <DataTableTd>
                        <DateDisplay iso={inv.due_date as string | undefined} />
                      </DataTableTd>
                      <DataTableTd align="right">
                        <CurrencyDisplay amount={String(inv.outstanding_amount)} />
                      </DataTableTd>
                      <DataTableTd className="text-muted">
                        {inv.aging_bucket ? agingBucketLabel(String(inv.aging_bucket)) : "—"}
                      </DataTableTd>
                      <DataTableTd>
                        <StatusBadge status={statusText} label={statusText} />
                      </DataTableTd>
                      <DataTableTd>
                        <Link href={`/invoices/${inv.id}`} className="text-sm font-medium no-underline">
                          View
                        </Link>
                      </DataTableTd>
                    </DataTableRow>
                  );
                })}
              </DataTableBody>
            </DataTable>
            {!rows.length ? (
              <div className="py-8">
                <EmptyState
                  title="No invoices found."
                  description={q ? "Try a different search." : "Upload PDFs from Import Invoices to get started."}
                  action={q ? undefined : <Link href="/imports">Go to imports</Link>}
                />
              </div>
            ) : null}
          </div>
        ) : null}
      </Card>
    </div>
  );
}