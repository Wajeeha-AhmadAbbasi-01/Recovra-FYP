"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function InvoicesPage() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.invoices(q).then((res) => setRows(res.data ?? []));
  }, [q]);

  return (
    <div>
      <PageHeader title="Invoices" subtitle="Accepted local-check invoices for this workspace." />
      <Card>
        <Input placeholder="Search invoice reference" value={q} onChange={(e) => setQ(e.target.value)} className="max-w-sm" />
        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-black/10 text-left text-muted">
                <th className="py-2 pr-4">Reference</th>
                <th className="py-2 pr-4">Due</th>
                <th className="py-2 pr-4">Outstanding</th>
                <th className="py-2 pr-4">Bucket</th>
                <th className="py-2"> </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((inv) => (
                <tr key={String(inv.id)} className="border-b border-black/5">
                  <td className="py-3 pr-4 font-medium">{String(inv.invoice_reference)}</td>
                  <td className="py-3 pr-4">{String(inv.due_date ?? "—")}</td>
                  <td className="py-3 pr-4">{String(inv.outstanding_amount)}</td>
                  <td className="py-3 pr-4">{String(inv.aging_bucket ?? "—")}</td>
                  <td className="py-3">
                    <Link href={`/invoices/${inv.id}`} className="text-sm">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {!rows.length ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-muted">
                    No accepted invoices yet. Upload PDFs from Imports.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}