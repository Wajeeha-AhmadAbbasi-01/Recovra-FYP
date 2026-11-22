"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import clsx from "clsx";

type Me = { user: { full_name: string; role: string }; tenant: { name: string } };

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: NavIconDashboard },
  { href: "/imports", label: "Imports", icon: NavIconImports },
  { href: "/invoices", label: "Invoices", icon: NavIconInvoices },
  { href: "/collections", label: "Collections", icon: NavIconCollections },
  { href: "/inbox", label: "Inbox", icon: NavIconInbox },
  { href: "/customers", label: "Customers", icon: NavIconCustomers },
  { href: "/team", label: "Team", icon: NavIconTeam, ownerOnly: true },
] as const;

function NavLink({
  href,
  label,
  icon: Icon,
  active,
  onNavigate,
}: {
  href: string;
  label: string;
  icon: () => React.ReactNode;
  active: boolean;
  onNavigate?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={clsx(
        "flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors",
        active ? "bg-accentSoft text-accent" : "text-muted hover:bg-canvas hover:text-ink",
      )}
    >
      <Icon />
      <span>{label}</span>
    </Link>
  );
}

function SidebarContent({
  me,
  pathname,
  onLogout,
  onNavigate,
}: {
  me: Me;
  pathname: string;
  onLogout: () => void;
  onNavigate?: () => void;
}) {
  return (
    <>
      <div className="border-b border-border px-5 py-5">
        <p className="text-sm font-semibold tracking-tight text-ink">RECOVRA</p>
        <p className="text-xs text-muted">Accounts Receivable Copilot</p>
        <div className="mt-4 rounded-lg border border-border bg-canvas px-3 py-2">
          <p className="truncate text-xs font-medium text-ink">{me.tenant.name}</p>
          <p className="truncate text-xs text-muted">{me.user.full_name}</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Workspace">
        {NAV.filter((item) => !("ownerOnly" in item) || !item.ownerOnly || me.user.role === "owner").map((item) => (
          <NavLink
            key={item.href}
            href={item.href}
            label={item.label}
            icon={item.icon}
            active={pathname === item.href || pathname.startsWith(`${item.href}/`)}
            onNavigate={onNavigate}
          />
        ))}
      </nav>
      <div className="border-t border-border p-4">
        <Button variant="ghost" className="w-full justify-start" onClick={onLogout}>
          Log out
        </Button>
      </div>
    </>
  );
}

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    api.me().then((res) => {
      if (!res.data) {
        router.replace("/login");
        return;
      }
      setMe(res.data as Me);
      setLoading(false);
    });
  }, [router]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  async function logout() {
    await api.logout();
    router.replace("/login");
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas text-sm text-muted">
        Loading workspace…
      </div>
    );
  }

  if (!me) return null;

  return (
    <div className="min-h-screen bg-canvas lg:flex">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-surface lg:flex">
        <SidebarContent me={me} pathname={pathname} onLogout={logout} />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <button
            type="button"
            className="absolute inset-0 bg-ink/40"
            aria-label="Close menu"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative flex h-full w-[min(100%,280px)] flex-col bg-surface shadow-xl">
            <SidebarContent me={me} pathname={pathname} onLogout={logout} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-3 border-b border-border bg-surface px-4 lg:hidden">
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border text-ink"
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav"
            onClick={() => setMobileOpen(true)}
          >
            <span className="sr-only">Open menu</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="text-sm font-semibold text-ink">RECOVRA</span>
        </header>
        <main className="flex-1 px-4 py-5 md:px-8 md:py-8">
          <div className="mx-auto w-full max-w-content">{children}</div>
        </main>
      </div>
    </div>
  );
}

function NavIconDashboard() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M4 13h7V4H4v9zm9 7h7V11h-7v9zM4 20h7v-5H4v5zm9-8h7V4h-7v8z" />
    </svg>
  );
}
function NavIconImports() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M12 16V4m0 0l-4 4m4-4l4 4M4 20h16" />
    </svg>
  );
}
function NavIconInvoices() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M8 4h8l4 4v12H4V4h4zm4 0v4h4" />
    </svg>
  );
}
function NavIconCustomers() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M16 11a4 4 0 10-8 0M4 20a8 8 0 0116 0" />
    </svg>
  );
}
function NavIconTeam() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M9 11a3 3 0 100-6 3 3 0 000 6zm6 0a3 3 0 100-6 3 3 0 000 6zM3 20a6 6 0 0112 0M15 14a5 5 0 015 4" />
    </svg>
  );
}
function NavIconCollections() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  );
}
function NavIconInbox() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M4 6h16v12H4V6zm0 0l8 6 8-6" />
    </svg>
  );
}