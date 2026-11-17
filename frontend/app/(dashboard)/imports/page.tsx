"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";

export default function ImportsPage() {
  const [results, setResults] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const list = e.target.files;
    if (!list?.length) return;
    setLoading(true);
    setError(null);
    const res = await api.uploadPdfs(list);
    setLoading(false);
    if (res.error) {
      setError(res.error.message);
      return;
    }
    setResults(res.data?.results ?? []);
  }

  return (
    <div>
      <PageHeader
        title="PDF imports"
        subtitle="Batch upload sales-tax invoice PDFs for local format checks (not FBR verification)."
      />
      <Card>
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-black/15 bg-canvas px-6 py-12 text-center">
          <span className="text-sm font-medium">Drop PDFs here or click to browse</span>
          <span className="mt-1 text-xs text-muted">Up to 10 files · text-based PDFs · one invoice per file</span>
          <input type="file" accept="application/pdf" multiple className="hidden" onChange={onUpload} disabled={loading} />
        </label>
        {loading ? <p className="mt-4 text-sm text-muted">Processing batch…</p> : null}
        {error ? <p className="mt-4 text-sm text-danger">{error}</p> : null}
        {results.length ? (
          <div className="mt-8 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-black/10 text-muted">
                  <th className="py-2 pr-4">File</th>
                  <th className="py-2 pr-4">Local check status</th>
                  <th className="py-2">Notes</th>
                </tr>
              </thead>
              <tbody>
                {results.map((row, idx) => (
                  <tr key={idx} className="border-b border-black/5">
                    <td className="py-3 pr-4">{String(row.filename)}</td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={String(row.local_status)} />
                    </td>
                    <td className="py-3 text-muted">
                      {Array.isArray(row.issues) && row.issues.length
                        ? String((row.issues as Array<{ message?: string }>)[0]?.message)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <p className="mt-6 text-xs text-muted">
          Invalid uploads?{" "}
          <a href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/imports/sample-invoice.pdf`}>
            Download illustrative sample (non-official)
          </a>
        </p>
      </Card>
    </div>
  );
}