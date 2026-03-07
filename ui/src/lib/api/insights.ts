import { api } from "./client";
import type {
  AgentTrendResponse,
  InsightsSummary,
  TopCve,
  TrendResponse,
} from "./types";

function qs(window: number, fixable?: boolean): string {
  const params = `window=${window}`;
  return fixable ? `${params}&fixable=true` : params;
}

export function fetchInsightsSummary(
  window: number,
  fixable?: boolean,
): Promise<InsightsSummary> {
  return api(`/api/v1/insights/summary?${qs(window, fixable)}`);
}

export function fetchInsightsTrend(
  window: number,
  fixable?: boolean,
): Promise<TrendResponse> {
  return api(`/api/v1/insights/trend?${qs(window, fixable)}`);
}

export function fetchAgentsTrend(
  window: number,
  fixable?: boolean,
): Promise<AgentTrendResponse> {
  return api(`/api/v1/insights/agents/trend?${qs(window, fixable)}`);
}

export function fetchTopCves(
  window: number,
  fixable?: boolean,
): Promise<TopCve[]> {
  return api(`/api/v1/insights/top-cves?${qs(window, fixable)}`);
}
