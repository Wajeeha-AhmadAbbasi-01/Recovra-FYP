"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function AcceptInvitePage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    const res = await api.acceptInvitation({
      token: params.token,
      full_name: String(fd.get("full_name")),
      password: String(fd.get("password")),
    });
    if (res.error) {
      setError(res.error.message ?? "Could not accept invitation");
      return;
    }
    router.push("/login?invited=1");
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md items-center px-6 py-12">
      <Card className="w-full">
        <h1 className="font-display text-3xl">Join workspace</h1>
        <p className="mt-2 text-sm text-muted">Set your name and password to accept the invitation.</p>
        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <Input name="full_name" placeholder="Full name" required />
          <Input name="password" type="password" placeholder="Password" minLength={8} required />
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <Button type="submit" className="w-full">
            Accept invitation
          </Button>
        </form>
      </Card>
    </div>
  );
}