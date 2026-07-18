import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("@/lib/firebase", () => ({
  auth: { currentUser: null },
  onAuthChange: (cb: (u: null) => void) => {
    cb(null);
    return () => {};
  },
}));

import { apiPost, QuotaError, isQuotaError } from "@/lib/api";

function mockFetchOnce(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      statusText: `HTTP ${status}`,
      json: async () => body,
    }),
  );
}

describe("quota errors", () => {
  beforeEach(() => vi.unstubAllGlobals());

  it("throws a typed QuotaError on 402", async () => {
    mockFetchOnce(402, {
      detail: {
        error: "quota_exceeded",
        resource: "analysis",
        limit: 5,
        used: 5,
        message: "You've reached the free limit of 5 analysiss. Join the Pro waitlist for unlimited access.",
      },
    });

    await expect(apiPost("/api/v1/analyze")).rejects.toBeInstanceOf(QuotaError);
  });

  it("carries the resource, limit and used counts", async () => {
    mockFetchOnce(402, {
      detail: {
        error: "quota_exceeded",
        resource: "project",
        limit: 2,
        used: 2,
        message: "nope",
      },
    });

    try {
      await apiPost("/api/v1/projects/");
      expect.unreachable("should have thrown");
    } catch (err) {
      expect(isQuotaError(err)).toBe(true);
      const q = err as QuotaError;
      expect(q.resource).toBe("project");
      expect(q.limit).toBe(2);
      expect(q.used).toBe(2);
      expect(q.message).toBe("nope");
    }
  });

  it("leaves non-quota errors as plain Errors", async () => {
    mockFetchOnce(500, { detail: "boom" });

    const err: any = await apiPost("/x").catch((e) => e);
    expect(isQuotaError(err)).toBe(false);
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toBe("boom");
  });

  it("still formats FastAPI validation arrays", async () => {
    mockFetchOnce(422, {
      detail: [{ loc: ["body", "email"], msg: "invalid email" }],
    });

    const err: any = await apiPost("/x").catch((e) => e);
    expect(isQuotaError(err)).toBe(false);
    expect(err.message).toContain("email: invalid email");
  });
});
