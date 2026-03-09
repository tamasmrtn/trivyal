import { api } from "./client";
import type {
  AgentTrendResponse,
  InsightsSummary,
  TopCve,
  TrendResponse,
} from "./types";

function qs(window: number, fixable?: boolean, agentId?: string): string {
  const params = new URLSearchParams({ window: String(window) });
  if (fixable) params.set("fixable", "true");
  if (agentId) params.set("agent_id", agentId);
  return params.toString();
}

export function fetchInsightsSummary(
  window: number,
  fixable?: boolean,
  agentId?: string,
): Promise<InsightsSummary> {
  return api(`/api/v1/insights/summary?${qs(window, fixable, agentId)}`);
}

export function fetchInsightsTrend(
  window: number,
  fixable?: boolean,
  agentId?: string,
): Promise<TrendResponse> {
  return api(`/api/v1/insights/trend?${qs(window, fixable, agentId)}`);
}

export function fetchAgentsTrend(
  window: number,
  fixable?: boolean,
  agentId?: string,
): Promise<AgentTrendResponse> {
  return api(`/api/v1/insights/agents/trend?${qs(window, fixable, agentId)}`);
}

export function fetchTopCves(
  window: number,
  fixable?: boolean,
  agentId?: string,
): Promise<TopCve[]> {
  return api(`/api/v1/insights/top-cves?${qs(window, fixable, agentId)}`);
}
