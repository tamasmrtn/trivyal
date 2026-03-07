import { api } from "./client";
import type { DashboardSummary } from "./types";

export function fetchDashboardSummary(fixable?: boolean) {
  const qs = fixable ? "?fixable=true" : "";
  return api<DashboardSummary>(`/api/v1/dashboard/summary${qs}`);
}
