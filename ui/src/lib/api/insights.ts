import { api } from "./client";
import type {
  AgentTrendResponse,
  InsightsSummary,
  TopCve,
  TrendResponse,
} from "./types";

export function fetchInsightsSummary(window: number): Promise<InsightsSummary> {
  return api(`/api/v1/insights/summary?window=${window}`);
}

export function fetchInsightsTrend(window: number): Promise<TrendResponse> {
  return api(`/api/v1/insights/trend?window=${window}`);
}

export function fetchAgentsTrend(window: number): Promise<AgentTrendResponse> {
  return api(`/api/v1/insights/agents/trend?window=${window}`);
}

export function fetchTopCves(window: number): Promise<TopCve[]> {
  return api(`/api/v1/insights/top-cves?window=${window}`);
}
