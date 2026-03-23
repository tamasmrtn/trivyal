import { describe, it, expect, beforeEach, vi } from "vitest";
import { api, ApiError } from "@/lib/api/client";

vi.mock("@/store/auth", () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ token: null })),
  },
}));

import { useAuthStore } from "@/store/auth";

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.mocked(useAuthStore.getState).mockReturnValue({
      token: null,
      setToken: vi.fn(),
      logout: vi.fn(),
    });
  });

  it("includes Authorization header when token exists", async () => {
    vi.mocked(useAuthStore.getState).mockReturnValue({
      token: "my-token",
      setToken: vi.fn(),
      logout: vi.fn(),
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: "ok" }),
    });
    globalThis.fetch = mockFetch;

    await api("/api/v1/test");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/test",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer my-token",
        }),
      }),
    );
  });

  it("omits Authorization header when no token", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: "ok" }),
    });
    globalThis.fetch = mockFetch;

    await api("/api/v1/test");

    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers).not.toHaveProperty("Authorization");
  });

  it("returns parsed JSON on success", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: "123", name: "test" }),
    });

    const result = await api("/api/v1/test");

    expect(result).toEqual({ id: "123", name: "test" });
  });

  it("returns undefined on 204 No Content", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    });

    const result = await api("/api/v1/test");

    expect(result).toBeUndefined();
  });

  it("throws ApiError with status and detail on non-ok response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      json: () =>
        Promise.resolve({ detail: "Validation error", code: "INVALID" }),
    });

    try {
      await api("/api/v1/test");
      expect.fail("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.detail).toBe("Validation error");
      expect(apiErr.code).toBe("INVALID");
    }
  });

  it("falls back to statusText when error body is unparseable", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: () => Promise.reject(new Error("not json")),
    });

    try {
      await api("/api/v1/test");
      expect.fail("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(500);
      expect(apiErr.detail).toBe("Internal Server Error");
    }
  });
});
