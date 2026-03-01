import { api } from "./client";
import type {
  AgentResponse,
  AgentRegistered,
  AgentStatus,
  PaginatedResponse,
} from "./types";

export function fetchAgents(params?: {
  status?: AgentStatus;
  page?: number;
  page_size?: number;
}) {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.page) search.set("page", String(params.page));
  if (params?.page_size) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return api<PaginatedResponse<AgentResponse>>(
    `/api/v1/agents${qs ? `?${qs}` : ""}`,
  );
}

export function createAgent(name: string) {
  return api<AgentRegistered>("/api/v1/agents", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function deleteAgent(id: string) {
  return api<void>(`/api/v1/agents/${id}`, { method: "DELETE" });
}
