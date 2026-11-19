import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-8">
        <div>
          <p className="font-semibold tracking-tight text-2xl font-semibold">Recovra</p>
          <p className="text-sm text-muted">Receivables clarity for Pakistani SMEs</p>
        </div>
        <div className="flex gap-3">
          <Link href="/login">
            <Button variant="secondary">Log in</Button>
          </Link>
          <Link href="/signup">
            <Button>Start free</Button>
          </Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-10 px-6 py-16 lg:grid-cols-2 lg:items-center">
        <div>
          <h1 className="font-semibold tracking-tight text-5xl leading-tight text-ink">
            Know what you are owed—without the banking-dashboard noise.
          </h1>
          <p className="mt-6 max-w-xl text-lg text-muted">
            Upload sales-tax invoice PDFs, run local format checks, and see receivables aging in one calm workspace.
            Local checks only—never confused with official FBR verification.
          </p>
          <div className="mt-8 flex gap-3">
            <Link href="/signup">
              <Button className="px-6 py-3 text-base">Create your business workspace</Button>
            </Link>
          </div>
        </div>
        <Card className="space-y-4">
          <p className="text-xs font-medium uppercase tracking-widest text-muted">Example preview (illustrative)</p>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-xl bg-canvas p-4">
              <p className="text-muted">Outstanding</p>
              <p className="text-2xl font-semibold">PKR 1.2M</p>
            </div>
            <div className="rounded-xl bg-canvas p-4">
              <p className="text-muted">61–90 days</p>
              <p className="text-2xl font-semibold">PKR 180k</p>
            </div>
          </div>
          <p className="text-xs text-muted">Sample numbers for marketing only—not live data.</p>
        </Card>
      </section>
    </div>
  );
}