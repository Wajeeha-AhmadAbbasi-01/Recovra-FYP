"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { SectionPanel } from "@/components/layout/section-panel";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";

export default function TeamPage() {
  const [members, setMembers] = useState<Array<Record<string, unknown>>>([]);
  const [invitations, setInvitations] = useState<Array<Record<string, unknown>>>([]);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    Promise.all([api.members(), api.invitations()]).then(([m, i]) => {
      setMembers(m.data ?? []);
      setInvitations(i.data ?? []);
    });
  }

  useEffect(() => {
    refresh();
  }, []);

  async function invite() {
    setError(null);
    setMessage(null);
    const res = await api.createInvitation(email);
    if (res.error) {
      setError(res.error.message ?? "Invite failed");
      return;
    }
    setMessage("Invitation sent. Check Mailpit at http://localhost:8025 in development.");
    setEmail("");
    refresh();
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Team" subtitle="Invite finance managers and view workspace members (owner only)." />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="text-lg font-semibold text-ink">Invite finance manager</h2>
          <p className="mt-1 text-sm text-muted">Send an email invitation to join this workspace.</p>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <Input placeholder="finance@recovra.test" value={email} onChange={(e) => setEmail(e.target.value)} />
            <Button onClick={invite} disabled={!email.trim()}>
              Send invite
            </Button>
          </div>
          {message ? <p className="mt-3 text-sm text-success">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}
        </Card>

        <SectionPanel title="Members" description="People with access to this workspace.">
          <ul className="divide-y divide-border text-sm">
            {members.map((m) => (
              <li key={String(m.id)} className="flex flex-wrap justify-between gap-2 py-3">
                <span className="font-medium">{String(m.full_name)}</span>
                <span className="text-muted">
                  {String(m.email)} · {String(m.role)}
                </span>
              </li>
            ))}
            {!members.length ? <li className="py-4 text-muted">No members yet.</li> : null}
          </ul>
        </SectionPanel>
      </div>

      <SectionPanel title="Invitations" description="Pending and recent invitations.">
        <ul className="divide-y divide-border text-sm">
          {invitations.map((i) => (
            <li key={String(i.id)} className="flex flex-wrap items-center justify-between gap-2 py-3">
              <span>{String(i.invited_email)}</span>
              <StatusBadge status={String(i.status)} label={String(i.status).replace(/_/g, " ")} />
            </li>
          ))}
          {!invitations.length ? <li className="py-4 text-muted">No invitations.</li> : null}
        </ul>
      </SectionPanel>
    </div>
  );
}