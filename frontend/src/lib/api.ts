import { auth, onAuthChange } from "@/lib/firebase";

function getBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  }

  const { protocol, hostname, port } = window.location;

  // 1. VS Code Port Forwarding / GitHub Codespaces (e.g. xxx-3000.app.dev)
  if (hostname.includes("-3000")) {
    return `${protocol}//${hostname.replace("-3000", "-8000")}`;
  }

  // 2. Gitpod Port Forwarding (e.g. 3000-xxx.gitpod.io)
  if (hostname.startsWith("3000-")) {
    return `${protocol}//${hostname.replace("3000-", "8000-")}`;
  }

  // 3. Local Development (e.g. localhost:3000, 127.0.0.1:3000)
  // Resolve 'localhost' to '127.0.0.1' to prevent IPv6 (::1) DNS resolution failures
  let apiHost = hostname;
  if (hostname === "localhost") {
    apiHost = "127.0.0.1";
  }

  if (port) {
    return `${protocol}//${apiHost}:8000`;
  }

  // 4. Default fallback
  return process.env.NEXT_PUBLIC_API_URL ?? `${protocol}//${apiHost}:8000`;
}

const BASE_URL = getBaseUrl();

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

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));

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
