"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { API_BASE_URL } from "@/lib/config";
import { overdueStatus } from "@/lib/format";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { DateDisplay } from "@/components/ui/date-display";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";

export default function InvoiceDetailPage() {
  const params = useParams<{ id: string }>();
  const [invoice, setInvoice] = useState<Record<string, unknown> | null>(null);
  const [promises, setPromises] = useState<Array<Record<string, unknown>>>([]);
  const [disputes, setDisputes] = useState<Array<Record<string, unknown>>>([]);
  const [timeline, setTimeline] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [promiseDate, setPromiseDate] = useState("");
  const [promiseNote, setPromiseNote] = useState("");
  const [disputeReason, setDisputeReason] = useState("");
  const [resolveNotes, setResolveNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const loadCollections = useCallback(() => {
    return Promise.all([
      api.invoicePromises(params.id),
      api.invoiceDisputes(params.id),
      api.invoiceTimeline(params.id),
    ]).then(([pRes, dRes, tRes]) => {
      if (!pRes.error) setPromises(pRes.data?.items ?? []);
      if (!dRes.error) setDisputes(dRes.data?.items ?? []);
      if (!tRes.error) setTimeline(tRes.data?.items ?? []);
    });
  }, [params.id]);

  useEffect(() => {
    api.invoice(params.id).then((res) => {
      if (res.error) setError(res.error.message ?? "Invoice not found");
      else setInvoice(res.data ?? null);
    });
    loadCollections();
  }, [params.id, loadCollections]);

  if (error) return <ErrorState message={error} />;
  if (!invoice) return <LoadingSkeleton className="h-40" />;

  const customer = invoice.customer as Record<string, unknown> | null;

  async function submitPromise() {
    if (!promiseDate) {
      setActionMsg("Choose a promised date.");
      return;
    }
    setBusy(true);
    setActionMsg(null);
    const res = await api.createPromise(params.id, {
      promised_date: promiseDate,
      note: promiseNote || undefined,
    });
    setBusy(false);
    if (res.error) {
      setActionMsg(res.error.message ?? "Could not record promise");
      return;
    }
    setPromiseNote("");
    setActionMsg(`Promise recorded (${String(res.data?.scheduling_effect)}). Confirm when ready.`);
    await loadCollections();
  }

  async function submitDispute() {
    if (!disputeReason.trim()) {
      setActionMsg("Enter a dispute reason.");
      return;
    }
    setBusy(true);
    setActionMsg(null);
    const res = await api.createDispute(params.id, { reason: disputeReason.trim() });
    setBusy(false);
    if (res.error) {
      setActionMsg(res.error.message ?? "Could not record dispute");
      return;
    }
    setDisputeReason("");
    setActionMsg(`Dispute recorded (${String(res.data?.scheduling_effect)}).`);
    await loadCollections();
  }

  async function confirmPromise(id: string) {
    setBusy(true);
    setActionMsg(null);
    const res = await api.patchPromise(id, { status: "CONFIRMED" });
    setBusy(false);
    if (res.error) {
      setActionMsg(res.error.message ?? "Could not confirm promise");
      return;
    }
    setActionMsg(`Promise confirmed. Scheduling: ${String(res.data?.scheduling_effect)}.`);
    await loadCollections();
  }

  async function resolvePromise(id: string) {
    setBusy(true);
    setActionMsg(null);
    const res = await api.patchPromise(id, { status: "FULFILLED" });
    setBusy(false);
    if (res.error) {
      setActionMsg(res.error.message ?? "Could not resolve promise");
      return;
    }
    setActionMsg("Promise marked fulfilled (hold released if applicable).");
    await loadCollections();
  }

  async function confirmDispute(id: string) {
    setBusy(true);
    setActionMsg(null);
    const res = await api.patchDispute(id, { status: "CONFIRMED" });
    setBusy(false);
    if (res.error) {
      setActionMsg(res.error.message ?? "Could not confirm dispute");
      return;
    }
    setActionMsg(`Dispute confirmed. Scheduling: ${String(res.data?.scheduling_effect)}.`);
    await loadCollections();
  }

  async function resolveDispute(id: string) {
    setBusy(true);
    setActionMsg(null);
    const note = resolveNotes[id]?.trim();
    const res = await api.patchDispute(id, {
      status: "RESOLVED",
      resolution_note: note || undefined,
    });
    setBusy(false);
    if (res.error) {
      setActionMsg(res.error.message ?? "Could not resolve dispute");
      return;
    }
    setActionMsg("Dispute resolved (hold released if applicable).");
    await loadCollections();
  }

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

      <Card className="mt-6 space-y-4">
        <h2 className="text-sm font-semibold text-ink">Collections</h2>
        <p className="text-sm text-muted">
          Record staff-side promise or dispute. Balances are not changed here.{" "}
          <Link href="/collections" className="text-accent">
            Open collections hub
          </Link>
        </p>
        {actionMsg ? <p className="text-sm">{actionMsg}</p> : null}

        {promises.length > 0 ? (
          <div className="space-y-3 rounded-lg border border-border p-4">
            <h3 className="text-sm font-medium">Existing promises</h3>
            <ul className="space-y-3 text-sm">
              {promises.map((p) => {
                const id = String(p.id);
                const status = String(p.status);
                return (
                  <li key={id} className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2">
                    <div>
                      <StatusBadge status={status} />
                      <span className="ml-2 text-muted">Due {String(p.promised_date)}</span>
                      {p.note ? <p className="mt-1 text-xs text-muted">{String(p.note)}</p> : null}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {status === "RECORDED" ? (
                        <Button type="button" onClick={() => confirmPromise(id)} disabled={busy}>
                          Confirm
                        </Button>
                      ) : null}
                      {status === "CONFIRMED" ? (
                        <Button type="button" variant="secondary" onClick={() => resolvePromise(id)} disabled={busy}>
                          Resolve
                        </Button>
                      ) : null}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}

        {disputes.length > 0 ? (
          <div className="space-y-3 rounded-lg border border-border p-4">
            <h3 className="text-sm font-medium">Existing disputes</h3>
            <ul className="space-y-3 text-sm">
              {disputes.map((d) => {
                const id = String(d.id);
                const status = String(d.status);
                return (
                  <li key={id} className="space-y-2 border-b border-border pb-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <StatusBadge status={status} />
                        <p className="mt-1">{String(d.reason)}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {status === "OPEN" ? (
                          <Button type="button" onClick={() => confirmDispute(id)} disabled={busy}>
                            Confirm
                          </Button>
                        ) : null}
                        {status === "CONFIRMED" ? (
                          <Button type="button" variant="secondary" onClick={() => resolveDispute(id)} disabled={busy}>
                            Resolve
                          </Button>
                        ) : null}
                      </div>
                    </div>
                    {status === "CONFIRMED" ? (
                      <input
                        className="w-full max-w-md rounded-md border border-border bg-canvas px-3 py-2 text-xs"
                        placeholder="Resolution note (optional)"
                        value={resolveNotes[id] ?? ""}
                        onChange={(e) => setResolveNotes((prev) => ({ ...prev, [id]: e.target.value }))}
                      />
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}

        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3 rounded-lg border border-border p-4">
            <h3 className="text-sm font-medium">Payment promise</h3>
            <label className="block text-xs text-muted">
              Promised date
              <input
                type="date"
                className="mt-1 w-full rounded-md border border-border bg-canvas px-3 py-2 text-sm"
                value={promiseDate}
                onChange={(e) => setPromiseDate(e.target.value)}
              />
            </label>
            <label className="block text-xs text-muted">
              Note (optional)
              <textarea
                className="mt-1 w-full rounded-md border border-border bg-canvas px-3 py-2 text-sm"
                rows={2}
                value={promiseNote}
                onChange={(e) => setPromiseNote(e.target.value)}
              />
            </label>
            <Button type="button" onClick={submitPromise} disabled={busy}>
              Record promise
            </Button>
          </div>
          <div className="space-y-3 rounded-lg border border-border p-4">
            <h3 className="text-sm font-medium">Dispute</h3>
            <label className="block text-xs text-muted">
              Reason
              <textarea
                className="mt-1 w-full rounded-md border border-border bg-canvas px-3 py-2 text-sm"
                rows={3}
                value={disputeReason}
                onChange={(e) => setDisputeReason(e.target.value)}
              />
            </label>
            <Button type="button" onClick={submitDispute} disabled={busy}>
              Record dispute
            </Button>
          </div>
        </div>
      </Card>

      <Card className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-ink">Activity timeline</h2>
        {timeline.length === 0 ? (
          <p className="text-sm text-muted">No collection events yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {timeline.map((ev) => (
              <li key={String(ev.id)} className="border-b border-border pb-2">
                <span className="text-muted">{String(ev.created_at).slice(0, 19)}</span>
                {" — "}
                {String(ev.summary ?? ev.action)}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <p className="mt-6">
        <Link href="/invoices">← Back to invoices</Link>
      </p>
    </div>
  );
}