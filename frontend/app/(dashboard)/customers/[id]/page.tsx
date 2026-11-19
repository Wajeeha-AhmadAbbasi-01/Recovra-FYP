"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { DateDisplay } from "@/components/ui/date-display";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { DashboardStatCard } from "@/components/ui/dashboard-stat-card";
import { DataTable, DataTableBody, DataTableHead, DataTableRow, DataTableTd, DataTableTh } from "@/components/ui/data-table";
import { StatusBadge } from "@/components/ui/status-badge";

export default function CustomerDetailPage() {
  const params = useParams<{ id: string }>();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.customer(params.id).then((res) => {
      if (res.error) {
        setError(res.error.message ?? "Customer not found");
        setLoading(false);
        return;
      }
      setData(res.data ?? null);
      setLoading(false);
    });
  }, [params.id]);

  if (loading) return <LoadingSkeleton className="h-40" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const summary = (data.summary as Record<string, unknown>) ?? {};
  const invoices = (data.invoices as Array<Record<string, unknown>>) ?? [];

  return (
    <div>
      <PageHeader title={String(data.business_name)} subtitle="Customer account and associated invoices." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-semibold">Customer information</h2>
          <dl className="mt-4 space-y-2 text-sm">
            <div>
              <dt className="text-muted">Name</dt>
              <dd>{String(data.business_name)}</dd>
            </div>
            <div>
              <dt className="text-muted">Recovra customer ID</dt>
              <dd className="font-mono text-xs">{String(data.id)}</dd>
            </div>
            <div>
              <dt className="text-muted">Buyer NTN</dt>
              <dd>{data.buyer_ntn ? String(data.buyer_ntn) : "Not provided"}</dd>
            </div>
            <div>
              <dt className="text-muted">Contact email</dt>
              <dd>{data.contact_email ? String(data.contact_email) : "Not provided"}</dd>
            </div>
            {data.address ? (
              <div>
                <dt className="text-muted">Address</dt>
                <dd>{String(data.address)}</dd>
              </div>
            ) : null}
          </dl>
        </Card>

        <div className="grid gap-4 sm:grid-cols-3">
          <DashboardStatCard label="Total invoices" value={String(summary.invoice_count ?? 0)} />
          <DashboardStatCard
            label="Outstanding (PKR)"
            value={<CurrencyDisplay amount={String(summary.outstanding_total ?? "0")} />}
          />
          <DashboardStatCard label="Overdue invoices" value={String(summary.overdue_count ?? 0)} />
        </div>
      </div>

      <Card className="mt-8">
        <h2 className="font-semibold">Associated invoices</h2>
        {!invoices.length ? (
          <div className="mt-4">
            <EmptyState title="No invoices for this customer." />
          </div>
        ) : (
          <motion-div className="mt-4">
            <DataTable>
              <DataTableHead>
                <DataTableRow>
                  <DataTableTh>Reference</DataTableTh>
                  <DataTableTh>Issue date</DataTableTh>
                  <DataTableTh>Due date</DataTableTh>
                  <DataTableTh align="right">Total</DataTableTh>
                  <DataTableTh align="right">Outstanding</DataTableTh>
                  <DataTableTh>Status</DataTableTh>
                  <DataTableTh>Action</DataTableTh>
                </DataTableRow>
              </DataTableHead>
              <DataTableBody>
                {invoices.map((inv) => (
                  <DataTableRow key={String(inv.id)}>
                    <DataTableTd className="font-mono text-xs font-medium">{String(inv.invoice_reference)}</DataTableTd>
                    <DataTableTd>
                      <DateDisplay iso={inv.issue_date as string} />
                    </DataTableTd>
                    <DataTableTd>
                      <DateDisplay iso={inv.due_date as string | undefined} />
                    </DataTableTd>
                    <DataTableTd align="right">
                      <CurrencyDisplay amount={String(inv.total_amount)} />
                    </DataTableTd>
                    <DataTableTd align="right">
                      <CurrencyDisplay amount={String(inv.outstanding_amount)} />
                    </DataTableTd>
                    <DataTableTd>
                      <StatusBadge status={String(inv.status)} label={String(inv.status)} />
                    </DataTableTd>
                    <DataTableTd>
                      <Link href={`/invoices/${inv.id}`} className="text-sm font-medium no-underline">
                        View
                      </Link>
                    </DataTableTd>
                  </DataTableRow>
                ))}
              </DataTableBody>
            </DataTable>
          </motion-div>
        )}
      </Card>

      <p className="mt-6">
        <Link href="/customers">← Back to customers</Link>
      </p>
    </div>
  );
}