"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import clsx from "clsx";

type Me = { user: { full_name: string; role: string }; tenant: { name: string } };

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/imports", label: "Imports" },
  { href: "/invoices", label: "Invoices" },
  { href: "/customers", label: "Customers" },
  { href: "/team", label: "Team", ownerOnly: true },
];

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.me().then((res) => {
      if (!res.data) {
        router.replace("/login");
        return;
      }
      setMe(res.data);
      setLoading(false);
    });
  }, [router]);

  async function logout() {
    await api.logout();
    router.replace("/login");
  }

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center text-muted">Loading workspace…</div>;
  }

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="border-r border-black/5 bg-surface p-6">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-widest text-muted">Workspace</p>
          <p className="font-display text-xl">{me?.tenant.name}</p>
          <p className="text-sm text-muted">{me?.user.full_name}</p>
        </div>
        <nav className="space-y-1">
          {NAV.filter((item) => !item.ownerOnly || me?.user.role === "owner").map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "block rounded-lg px-3 py-2 text-sm",
                pathname === item.href ? "bg-accentSoft font-medium text-ink" : "text-muted hover:bg-canvas hover:text-ink",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="mt-10">
          <Button variant="ghost" onClick={logout}>
            Log out
          </Button>
        </div>
      </aside>
      <main className="p-6 lg:p-10">{children}</main>
    </div>
  );
}