import { api } from "./client";
import type { DashboardSummary } from "./types";

export function fetchDashboardSummary() {
  return api<DashboardSummary>("/api/v1/dashboard/summary");
}
