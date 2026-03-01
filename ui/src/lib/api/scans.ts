import { api } from "./client";
import type { PaginatedResponse, ScanResultResponse } from "./types";

export interface ScanResultDetail extends ScanResultResponse {
  trivy_raw: Record<string, unknown> | null;
}

export function fetchScans(params?: { page?: number; page_size?: number }) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.page_size) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return api<PaginatedResponse<ScanResultResponse>>(
    `/api/v1/scans${qs ? `?${qs}` : ""}`,
  );
}

export function fetchAgentScans(
  agentId: string,
  params?: { page?: number; page_size?: number },
) {
  const search = new URLSearchParams();
  if (params?.page) search.set("page", String(params.page));
  if (params?.page_size) search.set("page_size", String(params.page_size));
  const qs = search.toString();
  return api<PaginatedResponse<ScanResultResponse>>(
    `/api/v1/agents/${agentId}/scans${qs ? `?${qs}` : ""}`,
  );
}

export function fetchScan(id: string) {
  return api<ScanResultDetail>(`/api/v1/scans/${id}`);
}

export function triggerScan(agentId: string) {
  return api<{ job_id: string }>(`/api/v1/agents/${agentId}/scans`, {
    method: "POST",
  });
}
