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
    cache: "no-store",
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

  importsRecent: () => json<Array<Record<string, unknown>>>("/api/v1/imports/recent"),

  members: () => json<Array<Record<string, unknown>>>("/api/v1/team/members"),

  invitations: () => json<Array<Record<string, unknown>>>("/api/v1/team/invitations"),

  createInvitation: (email: string) =>
    json("/api/v1/team/invitations", { method: "POST", body: JSON.stringify({ email }) }),

  acceptInvitation: (body: { token: string; full_name: string; password: string }) =>
    json("/api/v1/team/invitations/accept", { method: "POST", body: JSON.stringify(body) }),

  invoice: (id: string) => json<Record<string, unknown>>(`/api/v1/invoices/${id}`),

  collectionTasks: (params?: { status?: string; overdue?: boolean }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.overdue) qs.set("overdue", "true");
    const tail = qs.toString() ? `?${qs}` : "";
    return json<{ items: Array<Record<string, unknown>>; total: number }>(`/api/v1/collections/tasks${tail}`);
  },

  collectionTask: (id: string) => json<Record<string, unknown>>(`/api/v1/collections/tasks/${id}`),

  patchCollectionTask: (id: string, body: Record<string, unknown>) =>
    json<Record<string, unknown>>(`/api/v1/collections/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  createCollectionTask: (body: Record<string, unknown>) =>
    json<Record<string, unknown>>("/api/v1/collections/tasks", { method: "POST", body: JSON.stringify(body) }),

  reminderPreview: () =>
    json<{ items: Array<Record<string, unknown>>; sends_customer_email: boolean; note?: string }>(
      "/api/v1/collections/reminders/preview",
    ),

  runReminders: () =>
    json<Record<string, unknown>>("/api/v1/collections/reminders/run", { method: "POST", body: "{}" }),

  invoiceTimeline: (invoiceId: string) =>
    json<{ items: Array<Record<string, unknown>> }>(`/api/v1/collections/invoices/${invoiceId}/timeline`),

  invoicePromises: (invoiceId: string) =>
    json<{ items: Array<Record<string, unknown>>; total: number }>(
      `/api/v1/collections/invoices/${invoiceId}/promises`,
    ),

  invoiceDisputes: (invoiceId: string) =>
    json<{ items: Array<Record<string, unknown>>; total: number }>(
      `/api/v1/collections/invoices/${invoiceId}/disputes`,
    ),

  createPromise: (invoiceId: string, body: Record<string, unknown>) =>
    json<Record<string, unknown>>(`/api/v1/collections/invoices/${invoiceId}/promises`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  patchPromise: (promiseId: string, body: Record<string, unknown>) =>
    json<Record<string, unknown>>(`/api/v1/collections/promises/${promiseId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  createDispute: (invoiceId: string, body: Record<string, unknown>) =>
    json<Record<string, unknown>>(`/api/v1/collections/invoices/${invoiceId}/disputes`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  patchDispute: (disputeId: string, body: Record<string, unknown>) =>
    json<Record<string, unknown>>(`/api/v1/collections/disputes/${disputeId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  inboxStatus: () => json<Record<string, unknown>>("/api/v1/inbox/mailbox/status"),

  inboxMessages: () => json<{ items: Array<Record<string, unknown>>; total: number }>("/api/v1/inbox/messages"),

  inboxMessage: (id: string) => json<Record<string, unknown>>(`/api/v1/inbox/messages/${id}`),

  confirmInboxLink: (messageId: string, body: { invoice_id: string; action: "confirm" | "reject" }) =>
    json<Record<string, unknown>>(`/api/v1/inbox/messages/${messageId}/links`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  mockInboxDeliver: (body: { messages: Array<Record<string, unknown>> }) =>
    json<Record<string, unknown>>("/api/v1/inbox/mailbox/mock-deliver", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  uploadPdfs: async (files: FileList): Promise<ApiResult<{ results: Array<Record<string, unknown>> }>> => {
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    const res = await fetch(`${API_BASE_URL}/api/v1/imports/pdf-batch`, {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      body: form,
    });
    return res.json();
  },
};