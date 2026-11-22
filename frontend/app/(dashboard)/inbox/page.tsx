"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { DataTable, DataTableBody, DataTableHead, DataTableRow, DataTableTd, DataTableTh } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";

export default function InboxPage() {
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mockBusy, setMockBusy] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return Promise.all([api.inboxMessages(), api.inboxStatus()]).then(([mRes, sRes]) => {
      if (mRes.error) {
        setError(mRes.error.message ?? "Could not load messages");
        setLoading(false);
        return;
      }
      setItems(mRes.data?.items ?? []);
      setStatus(sRes.data ?? null);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function deliverSample() {
    setMockBusy(true);
    const now = new Date().toISOString();
    const res = await api.mockInboxDeliver({
      messages: [
        {
          uidvalidity: 1,
          uid: Math.floor(Math.random() * 1_000_000),
          sender: "payer@example.com",
          recipient: "collections@tenant.local",
          subject: "RE: Invoice reference in subject",
          body: "Please confirm payment for invoice REF-PLACEHOLDER",
          received_at: now,
          invoice_references: [],
        },
      ],
    });
    setMockBusy(false);
    if (res.error) {
      setError(res.error.message ?? "Mock deliver failed (dev only).");
      return;
    }
    await load();
  }

  return (
    <div>
      <PageHeader
        title="Inbox"
        subtitle="Inbound messages linked to invoices — mock ingest in development."
        disclaimer="No outbound mail. Live IMAP is not enabled unless separately approved."
      />
      {status ? (
        <p className="mb-4 text-sm text-muted">
          Provider: {String(status.provider)} · live IMAP: {String(status.live_imap)} · setting:{" "}
          {status.imap_enabled_setting ? "on" : "off"}
        </p>
      ) : null}
      <div className="mb-6 flex flex-wrap gap-3">
        <Button type="button" variant="secondary" onClick={() => load()} disabled={loading}>
          Refresh
        </Button>
        <Button type="button" variant="secondary" onClick={deliverSample} disabled={mockBusy}>
          {mockBusy ? "Delivering…" : "Mock deliver sample"}
        </Button>
      </div>
      {error ? <ErrorState message={error} /> : null}
      {loading ? <LoadingSkeleton className="h-40" /> : null}
      {!loading && !error ? (
        <Card>
          {items.length === 0 ? (
            <EmptyState title="No messages" description="Use mock deliver or ingest fixtures from Swagger." />
          ) : (
            <DataTable>
              <DataTableHead>
                <DataTableRow>
                  <DataTableTh>Received</DataTableTh>
                  <DataTableTh>From</DataTableTh>
                  <DataTableTh>Subject</DataTableTh>
                  <DataTableTh>Links</DataTableTh>
                  <DataTableTh />
                </DataTableRow>
              </DataTableHead>
              <DataTableBody>
                {items.map((m) => {
                  const links = (m.links as Array<Record<string, unknown>>) ?? [];
                  return (
                    <DataTableRow key={String(m.id)}>
                      <DataTableTd>{String(m.received_at).slice(0, 19)}</DataTableTd>
                      <DataTableTd>{String(m.sender)}</DataTableTd>
                      <DataTableTd>{String(m.subject)}</DataTableTd>
                      <DataTableTd>{links.length ? links.map((l) => l.link_state).join(", ") : "—"}</DataTableTd>
                      <DataTableTd>
                        <Link href={`/inbox/${m.id}`} className="text-sm font-medium text-accent">
                          Open
                        </Link>
                      </DataTableTd>
                    </DataTableRow>
                  );
                })}
              </DataTableBody>
            </DataTable>
          )}
        </Card>
      ) : null}
    </div>
  );
}