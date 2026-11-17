"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";

export default function CustomersPage() {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    api.customers().then((res) => setRows(res.data ?? []));
  }, []);

  return (
    <div>
      <PageHeader title="Customers" subtitle="Buyers linked from accepted invoice PDFs." />
      <Card>
        <ul className="divide-y divide-black/5">
          {rows.map((c) => (
            <li key={String(c.id)} className="flex justify-between py-3 text-sm">
              <span className="font-medium">{String(c.business_name)}</span>
              <span className="text-muted">{String(c.buyer_ntn ?? "—")}</span>
            </li>
          ))}
          {!rows.length ? <li className="py-6 text-center text-muted">No customers yet.</li> : null}
        </ul>
      </Card>
    </div>
  );
}