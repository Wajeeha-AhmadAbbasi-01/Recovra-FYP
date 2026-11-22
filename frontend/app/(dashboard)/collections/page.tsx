"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CurrencyDisplay } from "@/components/ui/currency-display";
import { DataTable, DataTableBody, DataTableHead, DataTableRow, DataTableTd, DataTableTh } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { StatusBadge } from "@/components/ui/status-badge";

export default function CollectionsPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Array<Record<string, unknown>>>([]);
  const [preview, setPreview] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runMsg, setRunMsg] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualInvoiceId, setManualInvoiceId] = useState("");
  const [manualReason, setManualReason] = useState("");
  const [manualBusy, setManualBusy] = useState(false);
  const [manualMsg, setManualMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return Promise.all([api.collectionTasks(), api.reminderPreview()]).then(([tRes, pRes]) => {
      if (tRes.error) {
        setError(tRes.error.message ?? "Could not load tasks");
        setLoading(false);
        return;
      }
      setTasks(tRes.data?.items ?? []);
      setPreview(pRes.data?.items?.slice(0, 8) ?? []);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function runCycle() {
    setRunning(true);
    setRunMsg(null);
    const res = await api.runReminders();
    setRunning(false);
    if (res.error) {
      setRunMsg(res.error.message ?? "Run failed");
      return;
    }
    const d = res.data as { tasks_created?: number; sends_customer_email?: boolean };
    setRunMsg(
      `Created ${d.tasks_created ?? 0} staff task(s). No customer email was sent.`,
    );
    await load();
  }

  async function createManualTask() {
    if (!manualInvoiceId.trim() || !manualReason.trim()) {
      setManualMsg("Invoice ID and reason are required.");
      return;
    }
    setManualBusy(true);
    setManualMsg(null);
    const res = await api.createCollectionTask({
      invoice_id: manualInvoiceId.trim(),
      task_type: "FOLLOW_UP",
      reason: manualReason.trim(),
    });
    setManualBusy(false);
    if (res.error) {
      setManualMsg(res.error.message ?? "Could not create task");
      return;
    }
    const taskId = String(res.data?.id ?? "");
    setManualMsg(taskId ? `Follow-up task created.` : "Follow-up task created.");
    setManualInvoiceId("");
    setManualReason("");
    setShowManualForm(false);
    await load();
    if (taskId) router.push(`/collections/tasks/${taskId}`);
  }

  return (
    <div>
      <PageHeader
        title="Collections"
        subtitle="Staff follow-up tasks and internal reminder scheduling only."
        disclaimer="Tasks do not send customer email. Invoice balances come from Module 1 only."
      />
      <h1 className="sr-only">Collections</h1>
      <div className="mb-6 flex flex-wrap gap-3">
        <Button type="button" variant="secondary" onClick={() => load()} disabled={loading}>
          Refresh
        </Button>
        <Button type="button" onClick={runCycle} disabled={running}>
          {running ? "Running…" : "Run reminder cycle"}
        </Button>
        <Button type="button" variant="secondary" onClick={() => setShowManualForm((v) => !v)}>
          {showManualForm ? "Hide manual task" : "Create manual task"}
        </Button>
      </div>
      {runMsg ? <p className="mb-4 text-sm text-muted">{runMsg}</p> : null}
      {manualMsg ? <p className="mb-4 text-sm text-muted">{manualMsg}</p> : null}

      {showManualForm ? (
        <Card className="mb-6 space-y-3">
          <h2 className="text-sm font-semibold text-ink">New FOLLOW_UP task</h2>
          <p className="text-xs text-muted">Copy the invoice UUID from an invoice detail page or the invoices list.</p>
          <label className="block text-xs text-muted">
            Invoice ID
            <input
              className="mt-1 w-full max-w-lg rounded-md border border-border bg-canvas px-3 py-2 text-sm font-mono"
              value={manualInvoiceId}
              onChange={(e) => setManualInvoiceId(e.target.value)}
              placeholder="00000000-0000-0000-0000-000000000000"
            />
          </label>
          <label className="block text-xs text-muted">
            Reason
            <textarea
              className="mt-1 w-full max-w-lg rounded-md border border-border bg-canvas px-3 py-2 text-sm"
              rows={3}
              value={manualReason}
              onChange={(e) => setManualReason(e.target.value)}
              placeholder="Why staff need to follow up"
            />
          </label>
          <Button type="button" onClick={createManualTask} disabled={manualBusy}>
            {manualBusy ? "Creating…" : "Create task"}
          </Button>
        </Card>
      ) : null}

      {error ? <ErrorState message={error} /> : null}
      {loading ? <LoadingSkeleton className="h-40" /> : null}

      {!loading && !error ? (
        <>
          <Card className="mb-6">
            <h2 className="mb-3 text-sm font-semibold text-ink">Reminder preview (sample)</h2>
            {preview.length === 0 ? (
              <EmptyState title="No invoices to preview" />
            ) : (
              <ul className="space-y-2 text-sm">
                {preview.map((row) => (
                  <li key={String(row.invoice_id)} className="flex flex-wrap justify-between gap-2 border-b border-border pb-2">
                    <span>{String(row.invoice_reference)}</span>
                    <span className="text-muted">
                      {String(row.decision)} — {String(row.reason)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <h2 className="mb-4 text-sm font-semibold text-ink">Follow-up tasks</h2>
            {tasks.length === 0 ? (
              <EmptyState title="No tasks yet" description="Run the reminder cycle or create a manual task." />
            ) : (
              <DataTable>
                <DataTableHead>
                  <DataTableRow>
                    <DataTableTh>Invoice</DataTableTh>
                    <DataTableTh>Type</DataTableTh>
                    <DataTableTh>Status</DataTableTh>
                    <DataTableTh>Source</DataTableTh>
                    <DataTableTh align="right">Outstanding</DataTableTh>
                    <DataTableTh />
                  </DataTableRow>
                </DataTableHead>
                <DataTableBody>
                  {tasks.map((t) => (
                    <DataTableRow key={String(t.id)}>
                      <DataTableTd>{String(t.invoice_reference)}</DataTableTd>
                      <DataTableTd>{String(t.task_type)}</DataTableTd>
                      <DataTableTd>
                        <StatusBadge status={String(t.status)} />
                      </DataTableTd>
                      <DataTableTd>{String(t.source)}</DataTableTd>
                      <DataTableTd align="right">
                        <CurrencyDisplay amount={String(t.outstanding_amount)} />
                      </DataTableTd>
                      <DataTableTd>
                        <Link href={`/collections/tasks/${t.id}`} className="text-sm font-medium text-accent">
                          Open
                        </Link>
                      </DataTableTd>
                    </DataTableRow>
                  ))}
                </DataTableBody>
              </DataTable>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}