"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { DataTable, DataTableBody, DataTableHead, DataTableRow, DataTableTd, DataTableTh } from "@/components/ui/data-table";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export default function CustomersPage() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.customers().then((res) => {
      if (res.error) {
        setError(res.error.message ?? "Could not load customers");
        setLoading(false);
        return;
      }
      setRows(res.data ?? []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton className="h-10 w-64" />
        <LoadingSkeleton className="h-48" />
      </div>
    );
  }

  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <PageHeader title="Customer Accounts" subtitle="Directory of buyers linked from accepted invoices and their balances." />
      <Card>
        {!rows.length ? (
          <EmptyState title="No customers yet." description="Customers appear when invoice PDFs are accepted." />
        ) : (
          <DataTable>
            <DataTableHead>
              <DataTableRow>
                <DataTableTh>Customer</DataTableTh>
                <DataTableTh>Customer ID</DataTableTh>
                <DataTableTh>Buyer NTN</DataTableTh>
                <DataTableTh>Contact email</DataTableTh>
                <DataTableTh align="right">Invoices</DataTableTh>
                <DataTableTh align="right">Outstanding</DataTableTh>
                <DataTableTh align="right">Overdue</DataTableTh>
                <DataTableTh>Action</DataTableTh>
              </DataTableRow>
            </DataTableHead>
            <DataTableBody>
              {rows.map((c) => (
                <DataTableRow key={String(c.id)}>
                  <DataTableTd className="font-medium">{String(c.business_name)}</DataTableTd>
                  <DataTableTd className="font-mono text-xs text-muted">{String(c.id).slice(0, 8)}…</DataTableTd>
                  <DataTableTd>{c.buyer_ntn ? String(c.buyer_ntn) : "Not provided"}</DataTableTd>
                  <DataTableTd>{c.contact_email ? String(c.contact_email) : "Not provided"}</DataTableTd>
                  <DataTableTd align="right">{String(c.invoice_count ?? 0)}</DataTableTd>
                  <DataTableTd align="right">
                    <CurrencyDisplay amount={String(c.outstanding_total ?? "0")} />
                  </DataTableTd>
                  <DataTableTd align="right">{String(c.overdue_count ?? 0)}</DataTableTd>
                  <DataTableTd>
                    <Link href={`/customers/${c.id}`} className="text-sm font-medium no-underline">
                      View details
                    </Link>
                  </DataTableTd>
                </DataTableRow>
              ))}
            </DataTableBody>
          </DataTable>
        )}
      </Card>
    </div>
  );
}