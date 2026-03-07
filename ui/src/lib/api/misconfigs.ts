import { api } from "./client";
import type {
  MisconfigFindingResponse,
  MisconfigStatus,
  PaginatedResponse,
  Severity,
} from "./types";
import type { RiskAcceptanceResponse } from "./findings";

export function fetchMisconfigs(params?: {
  severity?: Severity;
  status?: MisconfigStatus;
  agent_id?: string;
  container_id?: string;
  check_id?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}) {
  const search = new URLSearchParams();
  if (params?.severity) search.set("severity", params.severity);
  if (params?.status) search.set("status", params.status);
  if (params?.agent_id) search.set("agent_id", params.agent_id);
  if (params?.container_id) search.set("container_id", params.container_id);
  if (params?.check_id) search.set("check_id", params.check_id);
  if (params?.sort_by) search.set("sort_by", params.sort_by);
  if (params?.sort_dir) search.set("sort_dir", params.sort_dir);
  if (params?.page) search.set("page", String(params.page));
  if (params?.page_size) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return api<PaginatedResponse<MisconfigFindingResponse>>(
    `/api/v1/misconfigs${qs ? `?${qs}` : ""}`,
  );
}

export function fetchMisconfig(id: string) {
  return api<MisconfigFindingResponse>(`/api/v1/misconfigs/${id}`);
}

export function updateMisconfig(id: string, status: MisconfigStatus) {
  return api<MisconfigFindingResponse>(`/api/v1/misconfigs/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function createMisconfigAcceptance(findingId: string, reason: string) {
  return api<RiskAcceptanceResponse>(
    `/api/v1/misconfigs/${findingId}/acceptances`,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    },
  );
}

export function revokeMisconfigAcceptance(
  findingId: string,
  acceptanceId: string,
) {
  return api<void>(
    `/api/v1/misconfigs/${findingId}/acceptances/${acceptanceId}`,
    { method: "DELETE" },
  );
}
