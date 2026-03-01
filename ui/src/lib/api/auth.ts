import type { TokenResponse } from "./types";

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const res = await fetch("/api/v1/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? "Login failed");
  }

  return res.json() as Promise<TokenResponse>;
}
