"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/config";
import { overdueStatus } from "@/lib/format";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { DateDisplay } from "@/components/ui/date-display";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export default function InvoiceDetailPage() {
  const params = useParams<{ id: string }>();
  const [invoice, setInvoice] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/invoices/${params.id}`, { credentials: "include" })
      .then((r) => r.json())
      .then((j) => {
        if (j.error) setError(j.error.message ?? "Invoice not found");
        else setInvoice(j.data);
      })
      .catch(() => setError("Could not load invoice."));
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!invoice) return <LoadingSkeleton className="h-40" />;

  const customer = invoice.customer as Record<string, unknown> | null;

  return (
    <div>
      <PageHeader
        title={String(invoice.invoice_reference)}
        subtitle={String(invoice.local_check_note ?? "Local format check only; not FBR verified.")}
      />
      <Card className="space-y-3 text-sm">
        {customer ? (
          <p>
            <span className="text-muted">Customer:</span>{" "}
            <Link href={`/customers/${customer.id}`}>{String(customer.business_name)}</Link>
          </p>
        ) : null}
        <p>
          <span className="text-muted">Outstanding:</span>{" "}
          <CurrencyDisplay amount={String(invoice.outstanding_amount)} /> ({String(invoice.currency)})
        </p>
        <p>
          <span className="text-muted">Total amount:</span> <CurrencyDisplay amount={String(invoice.total_amount)} />
        </p>
        <p>
          <span className="text-muted">Issue date:</span> <DateDisplay iso={invoice.issue_date as string} />
        </p>
        <p>
          <span className="text-muted">Due date:</span> <DateDisplay iso={invoice.due_date as string | undefined} />
        </p>
        <p>
          <span className="text-muted">Status:</span> {overdueStatus(invoice.days_overdue as number | null)}
        </p>
        <a href={`${API_BASE_URL}/api/v1/invoices/${params.id}/document`} className="inline-block pt-2 text-sm font-medium">
          View source PDF
        </a>
      </Card>
      <p className="mt-6">
        <Link href="/invoices">← Back to invoices</Link>
      </p>
    </div>
  );
}