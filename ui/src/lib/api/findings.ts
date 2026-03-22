import { api } from "./client";
import type {
  FindingResponse,
  FindingStatus,
  PaginatedResponse,
  Severity,
} from "./types";

export function fetchFinding(id: string) {
  return api<FindingResponse>(`/api/v1/findings/${id}`);
}

export function fetchAcceptances(findingId: string) {
  return api<RiskAcceptanceResponse[]>(
    `/api/v1/findings/${findingId}/acceptances`,
  );
}

export interface RiskAcceptanceResponse {
  id: string;
  finding_id: string;
  reason: string;
  accepted_by: string;
  expires_at: string | null;
  created_at: string;
}

export function fetchFindings(params?: {
  severity?: Severity;
  status?: FindingStatus;
  agent_id?: string;
  cve_id?: string;
  package?: string;
  container_id?: string;
  image_name?: string;
  image_tag?: string;
  fixable?: boolean;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}) {
  const search = new URLSearchParams();
  if (params?.severity) search.set("severity", params.severity);
  if (params?.status) search.set("status", params.status);
  if (params?.agent_id) search.set("agent_id", params.agent_id);
  if (params?.cve_id) search.set("cve_id", params.cve_id);
  if (params?.package) search.set("package", params.package);
  if (params?.container_id) search.set("container_id", params.container_id);
  if (params?.image_name) search.set("image_name", params.image_name);
  if (params?.image_tag) search.set("image_tag", params.image_tag);
  if (params?.fixable) search.set("fixable", "true");
  if (params?.sort_by) search.set("sort_by", params.sort_by);
  if (params?.sort_dir) search.set("sort_dir", params.sort_dir);
  if (params?.page) search.set("page", String(params.page));
  if (params?.page_size) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return api<PaginatedResponse<FindingResponse>>(
    `/api/v1/findings${qs ? `?${qs}` : ""}`,
  );
}

export function updateFinding(id: string, status: FindingStatus) {
  return api<FindingResponse>(`/api/v1/findings/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function createAcceptance(
  findingId: string,
  reason: string,
  expiresAt?: string | null,
) {
  return api<RiskAcceptanceResponse>(
    `/api/v1/findings/${findingId}/acceptances`,
    {
      method: "POST",
      body: JSON.stringify({ reason, expires_at: expiresAt ?? null }),
    },
  );
}

export function revokeAcceptance(findingId: string, acceptanceId: string) {
  return api<void>(
    `/api/v1/findings/${findingId}/acceptances/${acceptanceId}`,
    { method: "DELETE" },
  );
}
