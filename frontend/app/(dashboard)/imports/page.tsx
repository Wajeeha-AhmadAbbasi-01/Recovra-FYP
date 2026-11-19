"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { API_BASE_URL } from "@/lib/config";
import { importStatusLabel, isImportAccepted, isImportDuplicate, isImportNeedsReview, isImportRejected } from "@/lib/labels";
import { notifyReceivablesChanged } from "@/lib/receivables-events";
import { ImportFindings } from "@/components/imports/import-findings";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { DataTable, DataTableBody, DataTableHead, DataTableRow, DataTableTd, DataTableTh } from "@/components/ui/data-table";
import { ErrorState } from "@/components/ui/error-state";
import { StatusBadge } from "@/components/ui/status-badge";

const MAX_FILES = 10;
const IMPORT_RESULTS_KEY = "recovra:last-import-results";

type SelectedFile = { id: string; file: File };

function isReceivablesSaved(row: Record<string, unknown>): boolean {
  if (row.receivables_saved === true) return true;
  return Boolean(row.invoice_id);
}

export default function ImportsPage() {
  const [queue, setQueue] = useState<SelectedFile[]>([]);
  const [results, setResults] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadRecent = useCallback(() => {
    api.importsRecent().then((res) => {
      if (res.data?.length) {
        setResults(res.data);
        try {
          sessionStorage.setItem(IMPORT_RESULTS_KEY, JSON.stringify(res.data));
        } catch {
          /* ignore quota */
        }
      }
    });
  }, []);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(IMPORT_RESULTS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Array<Record<string, unknown>>;
        if (parsed.length) setResults(parsed);
      }
    } catch {
      /* ignore */
    }
    loadRecent();
  }, [loadRecent]);

  const addFiles = useCallback((list: FileList | File[]) => {
    setError(null);
    const existing = new Set(queue.map((q) => q.file.name));
    const next: SelectedFile[] = [...queue];
    for (const file of Array.from(list)) {
      if (next.length >= MAX_FILES) {
        setError(`You can upload up to ${MAX_FILES} files per batch.`);
        break;
      }
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are supported.");
        continue;
      }
      if (existing.has(file.name)) continue;
      existing.add(file.name);
      next.push({ id: `${file.name}-${file.size}-${crypto.randomUUID()}`, file });
    }
    setQueue(next);
  }, [queue]);

  function removeFile(id: string) {
    setQueue((prev) => prev.filter((f) => f.id !== id));
  }

  const batchSummary = useMemo(() => {
    let accepted = 0;
    let rejected = 0;
    let duplicate = 0;
    let needsReview = 0;
    for (const row of results) {
      const status = String(row.local_status);
      if (isImportAccepted(status)) accepted += 1;
      else if (isImportDuplicate(status)) duplicate += 1;
      else if (isImportNeedsReview(status)) needsReview += 1;
      else if (isImportRejected(status)) rejected += 1;
      else rejected += 1;
    }
    return { total: results.length, accepted, rejected, duplicate, needsReview };
  }, [results]);

  async function onUpload() {
    if (!queue.length || loading) return;
    setLoading(true);
    setError(null);
    setResults([]);
    const dt = new DataTransfer();
    queue.forEach((q) => dt.items.add(q.file));
    const res = await api.uploadPdfs(dt.files);
    setLoading(false);
    if (res.error) {
      setError(res.error.message ?? "Upload failed. Check your connection and try again.");
      return;
    }
    const rows = res.data?.results ?? [];
    setResults(rows);
    setQueue([]);
    try {
      sessionStorage.setItem(IMPORT_RESULTS_KEY, JSON.stringify(rows));
    } catch {
      /* ignore */
    }
    loadRecent();
    const shouldRefresh = rows.some((r) => isReceivablesSaved(r));
    if (shouldRefresh) {
      setError(null);
      notifyReceivablesChanged();
    }
  }

  const hasNewAccepted = results.some((r) => isReceivablesSaved(r));
  const lastBatchNotSaved = results.some(
    (r) => !isReceivablesSaved(r) && (r.invoice_reference || r.buyer_name),
  );

  return (
    <div>
      <PageHeader
        title="Import Invoices"
        subtitle="Upload sales-tax invoice PDFs for local format checks before they appear in your receivables."
        disclaimer="Format checks do not constitute official FBR verification."
      />

      <Card>
        <div
          role="button"
          tabIndex={0}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
          }}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-card border-2 border-dashed px-6 py-12 text-center transition ${
            dragOver ? "border-accent bg-accentSoft" : "border-border bg-canvas"
          }`}
        >
          <svg className="mb-3 h-10 w-10 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6h.1a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-sm font-medium">Drag and drop PDF invoices here</p>
          <p className="mt-1 text-xs text-muted">Or use Browse Files · up to {MAX_FILES} per batch · one invoice per PDF · text-based PDFs only</p>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            multiple
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.length) addFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-3">
          <Button type="button" variant="secondary" onClick={() => inputRef.current?.click()} disabled={loading}>
            Browse Files
          </Button>
          <Button type="button" onClick={onUpload} disabled={loading || !queue.length}>
            {loading ? "Uploading…" : "Upload batch"}
          </Button>
        </div>

        {queue.length ? (
          <div className="mt-6">
            <p className="text-sm font-medium">
              Selected ({queue.length}/{MAX_FILES})
            </p>
            <ul className="mt-2 divide-y divide-border rounded-lg border border-border">
              {queue.map((item) => (
                <li key={item.id} className="flex items-center justify-between gap-4 px-4 py-2 text-sm">
                  <span className="truncate">{item.file.name}</span>
                  <button type="button" className="text-muted hover:text-ink" onClick={() => removeFile(item.id)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="mt-4 text-sm text-muted">No files selected.</p>
        )}

        {error ? <div className="mt-4"><ErrorState message={error} /></div> : null}
        {loading ? <p className="mt-4 text-sm text-muted">Processing batch… please wait.</p> : null}

        {lastBatchNotSaved ? (
          <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-ink">
            <strong>Not added to Dashboard.</strong> Extracted fields are shown for review, but only{" "}
            <span className="font-medium">Passed Local Validation</span> (with an invoice link) creates customers and
            invoices. Check the Status column and Findings — fix the PDF and upload again.
          </p>
        ) : null}

        {hasNewAccepted ? (
          <p className="mt-4 rounded-lg border border-border bg-canvas px-4 py-3 text-sm text-muted">
            Accepted invoices are saved to your workspace. Open{" "}
            <Link href="/invoices" className="font-medium no-underline">
              Invoices
            </Link>{" "}
            or the{" "}
            <Link href="/dashboard" className="font-medium no-underline">
              Dashboard
            </Link>{" "}
            to see updated totals.
          </p>
        ) : null}

        {results.length ? (
          <div className="mt-8 space-y-6">
            <p className="text-xs text-muted">Recent imports for this workspace (including past uploads).</p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {[
                { label: "Total submitted", value: batchSummary.total },
                { label: "Accepted", value: batchSummary.accepted, className: "text-success" },
                { label: "Needs manual review", value: batchSummary.needsReview, className: "text-warning" },
                { label: "Rejected", value: batchSummary.rejected, className: "text-danger" },
                { label: "Already imported", value: batchSummary.duplicate, className: "text-warning" },
              ].map((s) => (
                <div key={s.label} className="rounded-lg border border-border bg-canvas p-4">
                  <p className="text-xs font-medium text-muted">{s.label}</p>
                  <p className={`mt-1 text-xl font-semibold tabular-nums ${s.className ?? "text-ink"}`}>{s.value}</p>
                </div>
              ))}
            </div>

            <DataTable className="mt-6">
              <DataTableHead>
                <DataTableRow>
                  <DataTableTh>File</DataTableTh>
                  <DataTableTh>Status</DataTableTh>
                  <DataTableTh>Reference</DataTableTh>
                  <DataTableTh>Seller</DataTableTh>
                  <DataTableTh>Customer</DataTableTh>
                  <DataTableTh>Dates</DataTableTh>
                  <DataTableTh>Lines</DataTableTh>
                  <DataTableTh>Profile</DataTableTh>
                  <DataTableTh>Findings</DataTableTh>
                  <DataTableTh>Saved</DataTableTh>
                  <DataTableTh>Action</DataTableTh>
                </DataTableRow>
              </DataTableHead>
              <DataTableBody>
                {results.map((row, idx) => (
                  <DataTableRow key={String(row.upload_id ?? idx)}>
                    <DataTableTd className="max-w-[160px] truncate">{String(row.filename)}</DataTableTd>
                    <DataTableTd>
                      <StatusBadge status={String(row.local_status)} />
                      <p className="mt-1 max-w-[200px] text-xs text-muted">
                        {String(row.local_status_label ?? importStatusLabel(String(row.local_status)))}
                      </p>
                    </DataTableTd>
                    <DataTableTd className="font-mono text-xs">{String(row.invoice_reference ?? "—")}</DataTableTd>
                    <DataTableTd className="max-w-[120px] truncate">{String(row.seller_name ?? "—")}</DataTableTd>
                    <DataTableTd className="max-w-[120px] truncate">{String(row.buyer_name ?? "—")}</DataTableTd>
                    <DataTableTd className="text-xs text-muted">
                      {row.issue_date ? <span>{String(row.issue_date)}</span> : "—"}
                      {row.due_date ? <span className="block">Due {String(row.due_date)}</span> : null}
                    </DataTableTd>
                    <DataTableTd className="tabular-nums text-xs">
                      {row.line_item_count != null ? String(row.line_item_count) : "—"}
                    </DataTableTd>
                    <DataTableTd className="font-mono text-[10px] text-muted">
                      {String(row.validation_profile ?? "—")}
                    </DataTableTd>
                    <DataTableTd>
                      <ImportFindings issues={row.issues} warnings={row.warnings} />
                      {isImportRejected(String(row.local_status)) ? (
                        <p className="mt-1 text-xs text-muted">Correct fields in the PDF and upload again.</p>
                      ) : null}
                      {isImportNeedsReview(String(row.local_status)) ? (
                        <p className="mt-1 text-xs text-muted">Use a text-based PDF or add machine-readable labels.</p>
                      ) : null}
                      {isImportDuplicate(String(row.local_status)) ? (
                        <p className="mt-1 text-xs text-muted">
                          {row.duplicate_kind === "file"
                            ? "Same PDF bytes as a prior successful import."
                            : row.duplicate_kind === "invoice"
                              ? "Seller and invoice reference already in this workspace."
                              : "No new invoice was created."}
                        </p>
                      ) : null}
                    </DataTableTd>
                    <DataTableTd className="text-xs">
                      {isReceivablesSaved(row) ? (
                        <span className="font-medium text-success">Yes</span>
                      ) : (
                        <span className="text-muted">No</span>
                      )}
                    </DataTableTd>
                    <DataTableTd>
                      {row.invoice_id ? (
                        <Link href={`/invoices/${row.invoice_id}`} className="text-sm font-medium no-underline">
                          {isImportDuplicate(String(row.local_status)) ? "View existing invoice" : "View invoice"}
                        </Link>
                      ) : null}
                    </DataTableTd>
                  </DataTableRow>
                ))}
              </DataTableBody>
            </DataTable>
          </div>
        ) : null}

        <h2 className="mt-10 text-sm font-semibold">Download Sample Invoice Format</h2>
        <p className="mt-1 text-xs text-muted">Illustrative structure only — not an official FBR document.</p>
        <a
          href={`${API_BASE_URL}/api/v1/imports/sample-invoice.pdf`}
          className="mt-2 inline-block text-sm font-medium"
          download
        >
          Download Sample Invoice Format
        </a>
      </Card>
    </div>
  );
}