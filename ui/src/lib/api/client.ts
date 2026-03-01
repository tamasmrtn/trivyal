import { useAuthStore } from "@/store/auth";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public code?: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = useAuthStore.getState().token;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText, body.code);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
