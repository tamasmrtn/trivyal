import { describe, it, expect, beforeEach, vi } from "vitest";
import { login } from "@/lib/api/auth";

describe("Auth API", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("sends POST with username and password", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ access_token: "tok-123" }),
    });
    globalThis.fetch = mockFetch;

    await login("admin", "secret");

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "admin", password: "secret" }),
    });
  });

  it("returns token response on success", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ access_token: "tok-123" }),
    });

    const result = await login("admin", "secret");

    expect(result).toEqual({ access_token: "tok-123" });
  });

  it("throws error with detail from server on failure", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: "Unauthorized",
      json: () => Promise.resolve({ detail: "Invalid credentials" }),
    });

    await expect(login("admin", "wrong")).rejects.toThrow(
      "Invalid credentials",
    );
  });

  it("falls back to statusText when error body is unparseable", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: "Internal Server Error",
      json: () => Promise.reject(new Error("not json")),
    });

    await expect(login("admin", "wrong")).rejects.toThrow(
      "Internal Server Error",
    );
  });

  it("falls back to 'Login failed' when detail and statusText are both empty", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: "",
      json: () => Promise.resolve({}),
    });

    await expect(login("admin", "wrong")).rejects.toThrow("Login failed");
  });
});
