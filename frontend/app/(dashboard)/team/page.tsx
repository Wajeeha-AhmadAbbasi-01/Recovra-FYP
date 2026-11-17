"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

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
    <div>
      <PageHeader title="Team" subtitle="Owner-only: invite a finance manager to this workspace." />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="font-medium">Invite finance manager</h2>
          <div className="mt-4 flex gap-2">
            <Input placeholder="finance@recovra.test" value={email} onChange={(e) => setEmail(e.target.value)} />
            <Button onClick={invite}>Send</Button>
          </div>
          {message ? <p className="mt-3 text-sm text-success">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}
        </Card>
        <Card>
          <h2 className="font-medium">Members</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {members.map((m) => (
              <li key={String(m.id)}>
                {String(m.full_name)} — {String(m.email)} ({String(m.role)})
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <Card className="mt-6">
        <h2 className="font-medium">Invitations</h2>
        <ul className="mt-4 space-y-2 text-sm text-muted">
          {invitations.map((i) => (
            <li key={String(i.id)}>
              {String(i.invited_email)} — {String(i.status)}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}