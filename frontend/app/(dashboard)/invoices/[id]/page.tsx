"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/config";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";

export default function InvoiceDetailPage() {
  const params = useParams<{ id: string }>();
  const [invoice, setInvoice] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/invoices/${params.id}`, { credentials: "include" })
      .then((r) => r.json())
      .then((j) => setInvoice(j.data));
  }, [params.id]);

  if (!invoice) return <p className="text-muted">Loading…</p>;

  return (
    <div>
      <PageHeader
        title={String(invoice.invoice_reference)}
        subtitle={String(invoice.local_check_note ?? "Local format check only; not FBR verified.")}
      />
      <Card className="space-y-2 text-sm">
        <p>
          <span className="text-muted">Outstanding:</span> {String(invoice.outstanding_amount)} {String(invoice.currency)}
        </p>
        <p>
          <span className="text-muted">Issue date:</span> {String(invoice.issue_date)}
        </p>
        <p>
          <span className="text-muted">Due date:</span> {String(invoice.due_date)}
        </p>
        <p>
          <span className="text-muted">Days overdue:</span> {String(invoice.days_overdue ?? 0)}
        </p>
        <a href={`${API_BASE_URL}/api/v1/invoices/${params.id}/document`} className="inline-block pt-4 text-sm">
          View source PDF
        </a>
      </Card>
    </div>
  );
}