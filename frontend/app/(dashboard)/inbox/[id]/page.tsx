"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";

export default function InboxMessagePage() {
  const params = useParams<{ id: string }>();
  const [message, setMessage] = useState<Record<string, unknown> | null>(null);
  const [invoiceId, setInvoiceId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    return api.inboxMessage(params.id).then((res) => {
      if (res.error) {
        setError(res.error.message ?? "Message not found");
        return;
      }
      const data = res.data ?? null;
      setMessage(data);
      const links = (data?.links as Array<Record<string, unknown>>) ?? [];
      const suggested = links.find((l) => String(l.link_state) === "SUGGESTED");
      if (suggested?.invoice_id) {
        setInvoiceId(String(suggested.invoice_id));
      }
    });
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function decide(invoiceUuid: string, action: "confirm" | "reject", previousState?: string) {
    if (!invoiceUuid.trim()) {
      setError("Invoice ID is required.");
      return;
    }
    setBusy(true);
    setError(null);
    setMsg(null);
    const res = await api.confirmInboxLink(params.id, { invoice_id: invoiceUuid.trim(), action });
    setBusy(false);
    if (res.error) {
      setError(res.error.message ?? "Link failed");
      return;
    }
    const after = String(res.data?.link_state ?? (action === "confirm" ? "CONFIRMED" : "REJECTED"));
    const before = previousState ?? "SUGGESTED";
    if (action === "confirm") {
      setMsg(`Link updated: ${before} → ${after}. Invoice link is now confirmed.`);
    } else {
      setMsg(`Link updated: ${before} → ${after}.`);
    }
    await load();
  }

  if (error && !message) return <ErrorState message={error} />;
  if (!message) return <LoadingSkeleton className="h-40" />;

  const links = (message.links as Array<Record<string, unknown>>) ?? [];

  return (
    <div>
      <PageHeader title={String(message.subject || "Message")} subtitle={`From ${message.sender}`} />
      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}
      {msg ? (
        <p className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-success" role="status">
          {msg}
        </p>
      ) : null}
      <Card className="mb-6 space-y-2 text-sm">
        <p>
          <span className="text-muted">Received:</span> {String(message.received_at)}
        </p>
        <p className="whitespace-pre-wrap border-t border-border pt-3">{String(message.body_text ?? "")}</p>
      </Card>

      <Card className="mb-6">
        <h2 className="mb-3 text-sm font-semibold">Invoice links</h2>
        {links.length === 0 ? (
          <p className="text-sm text-muted">No suggested links yet. Link manually below.</p>
        ) : (
          <ul className="space-y-4 text-sm">
            {links.map((l) => {
              const state = String(l.link_state);
              const invId = String(l.invoice_id);
              const ref = (l.evidence as Record<string, unknown> | undefined)?.match;
              return (
                <li key={String(l.id)} className="rounded-lg border border-border p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <StatusBadge status={state} label={state} />
                      <span className="ml-2">
                        Invoice{" "}
                        <Link href={`/invoices/${invId}`} className="font-medium text-accent">
                          {invId}
                        </Link>
                      </span>
                      {ref ? <span className="ml-2 text-xs text-muted">({String(ref)})</span> : null}
                    </div>
                    {state === "SUGGESTED" ? (
                      <div className="flex flex-wrap gap-2">
                        <Button type="button" onClick={() => decide(invId, "confirm", state)} disabled={busy}>
                          Confirm link
                        </Button>
                        <Button type="button" variant="secondary" onClick={() => decide(invId, "reject", state)} disabled={busy}>
                          Reject
                        </Button>
                      </div>
                    ) : null}
                  </div>
                  {state === "CONFIRMED" ? (
                    <p className="mt-2 text-xs text-muted">Staff confirmed this message matches the invoice.</p>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      <Card className="space-y-3">
        <h2 className="text-sm font-semibold">Link to another invoice</h2>
        <p className="text-xs text-muted">Use when mock ingest did not suggest a match, or to confirm a different invoice.</p>
        <input
          className="w-full max-w-md rounded-md border border-border bg-canvas px-3 py-2 text-sm font-mono"
          placeholder="Invoice UUID"
          value={invoiceId}
          onChange={(e) => setInvoiceId(e.target.value)}
        />
        <div className="flex gap-3">
          <Button type="button" onClick={() => decide(invoiceId, "confirm")} disabled={busy}>
            Confirm link
          </Button>
          <Button type="button" variant="secondary" onClick={() => decide(invoiceId, "reject")} disabled={busy}>
            Reject link
          </Button>
        </div>
      </Card>

      <p className="mt-6">
        <Link href="/inbox">← Back to inbox</Link>
      </p>
    </div>
  );
}