"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setRegistered(new URLSearchParams(window.location.search).has("registered"));
    }
  }, []);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    const res = await api.login({ email: String(fd.get("email")), password: String(fd.get("password")) });
    if (res.error) {
      setError(res.error.message ?? "Invalid credentials");
      return;
    }
    router.push("/dashboard");
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md items-center px-6 py-12">
      <Card className="w-full">
        <h1 className="font-display text-3xl">Welcome back</h1>
        {registered ? (
          <p className="mt-2 text-sm text-success">Account created. Sign in to continue.</p>
        ) : (
          <p className="mt-2 text-sm text-muted">Use the email and password from registration.</p>
        )}
        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <Input name="email" type="email" placeholder="Email" required />
          <Input name="password" type="password" placeholder="Password" required />
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <Button type="submit" className="w-full">
            Sign in
          </Button>
        </form>
        <p className="mt-6 text-sm text-muted">
          New business?{" "}
          <Link href="/signup" className="text-ink">
            Register
          </Link>
        </p>
      </Card>
    </div>
  );
}