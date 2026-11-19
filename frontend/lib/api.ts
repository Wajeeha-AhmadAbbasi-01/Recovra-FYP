import { API_BASE_URL } from "./config";

export type ApiError = {
  code?: string;
  message?: string;
  details?: Record<string, unknown>;
};

export type ApiResult<T> = {
  data: T | null;
  error: ApiError | null;
  meta?: { request_id: string };
};

async function json<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  return res.json() as Promise<ApiResult<T>>;
}

export const api = {
  register: (body: Record<string, string>) =>
    json("/api/v1/auth/register", { method: "POST", body: JSON.stringify(body) }),

  login: (body: { email: string; password: string }) =>
    json("/api/v1/auth/login", { method: "POST", body: JSON.stringify(body) }),

  logout: () => json("/api/v1/auth/logout", { method: "POST" }),

  me: () => json<Record<string, unknown>>("/api/v1/auth/me"),

  customers: () => json<Array<Record<string, unknown>>>("/api/v1/customers"),

  customer: (id: string) => json<Record<string, unknown>>(`/api/v1/customers/${id}`),

  invoices: (q?: string) =>
    json<Array<Record<string, unknown>>>(
      q ? `/api/v1/invoices?q=${encodeURIComponent(q)}` : "/api/v1/invoices",
    ),

  dashboardSummary: () => json<Record<string, unknown>>("/api/v1/dashboard/summary"),

  dashboardAging: () =>
    json<{ buckets: Record<string, string>; bucket_counts?: Record<string, number> }>("/api/v1/dashboard/aging"),

  dashboardOverdue: () => json<Array<Record<string, unknown>>>("/api/v1/dashboard/overdue-invoices"),

  members: () => json<Array<Record<string, unknown>>>("/api/v1/team/members"),

  invitations: () => json<Array<Record<string, unknown>>>("/api/v1/team/invitations"),

  createInvitation: (email: string) =>
    json("/api/v1/team/invitations", { method: "POST", body: JSON.stringify({ email }) }),

  acceptInvitation: (body: { token: string; full_name: string; password: string }) =>
    json("/api/v1/team/invitations/accept", { method: "POST", body: JSON.stringify(body) }),

  uploadPdfs: async (files: FileList): Promise<ApiResult<{ results: Array<Record<string, unknown>> }>> => {
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    const res = await fetch(`${API_BASE_URL}/api/v1/imports/pdf-batch`, {
      method: "POST",
      credentials: "include",
      body: form,
    });
    return res.json();
  },
};