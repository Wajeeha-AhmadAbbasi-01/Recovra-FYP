"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SignupPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    const password = String(fd.get("password"));
    const confirm = String(fd.get("confirm_password"));
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    const res = await api.register({
      business_name: String(fd.get("business_name")),
      full_name: String(fd.get("full_name")),
      email: String(fd.get("email")),
      password,
    });
    setLoading(false);
    if (res.error) {
      setError(res.error.message ?? "Registration failed");
      return;
    }
    router.push("/login?registered=1");
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-lg items-center px-6 py-12">
      <Card className="w-full">
        <h1 className="text-2xl font-semibold tracking-tight">Create your workspace</h1>
        <p className="mt-2 text-sm text-muted">Register your business, then sign in with the same email.</p>
        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <Input name="business_name" placeholder="Business name" required />
          <Input name="full_name" placeholder="Your full name" required />
          <Input name="email" type="email" placeholder="Work email" required />
          <Input name="password" type="password" placeholder="Password (min 8 chars)" minLength={8} required />
          <Input name="confirm_password" type="password" placeholder="Confirm password" minLength={8} required />
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Creating…" : "Create account"}
          </Button>
        </form>
        <p className="mt-6 text-sm text-muted">
          Already registered?{" "}
          <Link href="/login" className="text-ink">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}