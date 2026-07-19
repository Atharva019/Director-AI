import { auth, onAuthChange } from "@/lib/firebase";

function getBaseUrl(): string {
  // In the browser every call is same-origin: `/api/v1/...` is proxied to the
  // real backend by the rewrite in next.config.ts (target: API_PROXY_ORIGIN).
  //
  // This is deliberate rather than pointing fetch straight at the backend
  // host. Same-origin requests are not subject to CORS at all, so a wrong or
  // trailing-slashed CORS_ORIGINS can no longer take the whole app down — and
  // the previous host-guessing heuristic built `https://<app>.vercel.app:8000`
  // in production, which nothing listens on ("Failed to fetch" on every call).
  if (typeof window !== "undefined") return "";

  // Server components have no origin to be relative to, so they need the
  // absolute backend URL.
  return process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
}

export const BASE_URL = getBaseUrl();

// Helper to retrieve the current auth token, waiting for initialization if needed
async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  // 1. If currentUser is already populated, get the token immediately
  if (auth.currentUser) {
    return auth.currentUser.getIdToken();
  }

  // 2. Otherwise, wait for onAuthChange to resolve
  return new Promise((resolve) => {
    let resolved = false;
    let unsubscribe: (() => void) | null = null;

    unsubscribe = onAuthChange((user) => {
      if (unsubscribe) {
        unsubscribe();
      } else {
        // Safe fallback if the callback runs synchronously before unsubscribe is returned
        setTimeout(() => unsubscribe?.(), 0);
      }

      if (!resolved) {
        resolved = true;
        resolve(user ? user.getIdToken() : null);
      }
    });

    // Timeout fallback (5 seconds) to prevent hanging
    setTimeout(() => {
      if (!resolved) {
        resolved = true;
        resolve(null);
      }
    }, 5000);
  });
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const token = await getAuthToken();
  if (!token) return { "Content-Type": "application/json" };
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

/** Free-tier limit hit. The backend answers 402 with a structured detail. */
export class QuotaError extends Error {
  readonly resource: "analysis" | "project";
  readonly limit: number;
  readonly used: number;

  constructor(detail: {
    resource: "analysis" | "project";
    limit: number;
    used: number;
    message: string;
  }) {
    super(detail.message);
    this.name = "QuotaError";
    this.resource = detail.resource;
    this.limit = detail.limit;
    this.used = detail.used;
  }
}

export function isQuotaError(err: unknown): err is QuotaError {
  return err instanceof QuotaError;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));

    // Quota exhaustion is the one error the UI acts on rather than just
    // displays — surface it as its own type so callers can open the upgrade
    // prompt instead of string-matching a message.
    if (
      res.status === 402 &&
      body.detail &&
      typeof body.detail === "object" &&
      body.detail.error === "quota_exceeded"
    ) {
      throw new QuotaError(body.detail);
    }

    // FastAPI validation errors return detail as an array of objects:
    // [{loc: ["body", "field"], msg: "...", type: "..."}, ...]
    let message: string;
    if (Array.isArray(body.detail)) {
      message = body.detail
        .map((e: { loc?: string[]; msg?: string }) => {
          const field = e.loc?.slice(-1)[0] ?? "field";
          return `${field}: ${e.msg ?? "invalid"}`;
        })
        .join(", ");
    } else if (typeof body.detail === "string") {
      message = body.detail;
    } else {
      message = `HTTP ${res.status}`;
    }

    throw new Error(message);
  }
  return res.json() as Promise<T>;
}


// ─── Public API ─────────────────────────────────────────────────────────────

export async function apiGet<T>(path: string): Promise<T> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${BASE_URL}${path}`, { headers });
  return handleResponse<T>(res);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(body),
  });
  return handleResponse<T>(res);
}

export async function apiDel<T = void>(path: string): Promise<T> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers,
  });
  return handleResponse<T>(res);
}

/** Multipart upload (for image analysis) */
export async function apiUpload<T>(path: string, file: File, extraFields?: Record<string, string>): Promise<T> {
  const token = await getAuthToken() ?? "";
  const form = new FormData();
  form.append("file", file);
  if (extraFields) {
    for (const [k, v] of Object.entries(extraFields)) {
      form.append(k, v);
    }
  }
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  return handleResponse<T>(res);
}
