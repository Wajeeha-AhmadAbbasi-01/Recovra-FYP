"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";

const STATUSES = ["OPEN", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"] as const;

export default function CollectionTaskDetailPage() {
  const params = useParams<{ id: string }>();
  const [task, setTask] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string>("OPEN");

  const load = useCallback(() => {
    return api.collectionTask(params.id).then((res) => {
      if (res.error) {
        setError(res.error.message ?? "Task not found");
        return;
      }
      setTask(res.data ?? null);
      setStatus(String(res.data?.status ?? "OPEN"));
    });
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function saveStatus() {
    setSaving(true);
    const res = await api.patchCollectionTask(params.id, { status });
    setSaving(false);
    if (res.error) {
      setError(res.error.message ?? "Update failed");
      return;
    }
    setTask(res.data ?? null);
  }

  if (error && !task) return <ErrorState message={error} />;
  if (!task) return <LoadingSkeleton className="h-40" />;

  const invoiceId = String(task.invoice_id);

  return (
    <div>
      <PageHeader
        title={`Task — ${task.task_type}`}
        subtitle={String(task.reason)}
        disclaimer="Staff workflow only; no customer email is sent from this screen."
      />
      {error ? <p className="mb-4 text-sm text-danger">{error}</p> : null}
      <Card className="mb-6 space-y-3 text-sm">
        <p>
          <span className="text-muted">Invoice:</span>{" "}
          <Link href={`/invoices/${invoiceId}`} className="font-medium text-accent">
            {String(task.invoice_reference)}
          </Link>
        </p>
        <p>
          <span className="text-muted">Customer:</span> {String(task.customer_name)}
        </p>
        <p>
          <span className="text-muted">Outstanding:</span>{" "}
          <CurrencyDisplay amount={String(task.outstanding_amount)} />
        </p>
        <p>
          <span className="text-muted">Current status:</span> <StatusBadge status={String(task.status)} />
        </p>
        <p>
          <span className="text-muted">Source:</span> {String(task.source)} · {String(task.policy_version)}
        </p>
        {task.dedupe_key ? (
          <p className="text-xs text-muted break-all">Dedupe: {String(task.dedupe_key)}</p>
        ) : null}
      </Card>

      <Card className="space-y-4">
        <h2 className="text-sm font-semibold text-ink">Update status</h2>
        <select
          className="w-full max-w-xs rounded-md border border-border bg-canvas px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ")}
            </option>
          ))}
        </select>
        <Button type="button" onClick={saveStatus} disabled={saving}>
          {saving ? "Saving…" : "Save"}
        </Button>
      </Card>

      <p className="mt-6">
        <Link href="/collections">← Back to collections</Link>
      </p>
    </div>
  );
}