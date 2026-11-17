"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";

export default function DashboardPage() {
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [aging, setAging] = useState<Record<string, string>>({});

  useEffect(() => {
    Promise.all([api.dashboardSummary(), api.dashboardAging()]).then(([s, a]) => {
      setSummary(s.data ?? null);
      setAging(a.data?.buckets ?? {});
    });
  }, []);

  return (
    <div>
      <PageHeader
        title="Receivables overview"
        subtitle="Totals from locally accepted invoices only. This is not FBR verification."
      />
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-sm text-muted">Active invoices</p>
          <p className="mt-2 text-3xl font-semibold">{String(summary?.invoice_count ?? "—")}</p>
        </Card>
        <Card>
          <p className="text-sm text-muted">Total outstanding (PKR)</p>
          <p className="mt-2 text-3xl font-semibold">{String(summary?.total_outstanding ?? "0")}</p>
        </Card>
        <Card>
          <p className="text-sm text-muted">As of</p>
          <p className="mt-2 text-xl">{String(summary?.as_of_date ?? "—")}</p>
        </Card>
      </div>
      <Card className="mt-8">
        <h2 className="font-medium">Aging (Asia/Karachi)</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-5">
          {Object.entries(aging).map(([bucket, amount]) => (
            <div key={bucket} className="rounded-xl bg-canvas p-4">
              <p className="text-xs uppercase tracking-wide text-muted">{bucket.replace(/_/g, " ")}</p>
              <p className="mt-1 text-lg font-semibold">{amount}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}