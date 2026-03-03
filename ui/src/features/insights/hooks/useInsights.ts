import { useEffect, useState } from "react";
import {
  fetchAgentsTrend,
  fetchInsightsSummary,
  fetchInsightsTrend,
  fetchTopCves,
} from "@/lib/api/insights";
import type {
  AgentTrendResponse,
  InsightsSummary,
  TopCve,
  TrendResponse,
} from "@/lib/api/types";

interface InsightsData {
  summary: InsightsSummary;
  trend: TrendResponse;
  agentsTrend: AgentTrendResponse;
  topCves: TopCve[];
}

export function useInsights(window: number) {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchInsightsSummary(window),
      fetchInsightsTrend(window),
      fetchAgentsTrend(window),
      fetchTopCves(window),
    ])
      .then(([summary, trend, agentsTrend, topCves]) => {
        if (!cancelled) {
          setData({ summary, trend, agentsTrend, topCves });
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load insights",
          );
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [window]);

  return { data, loading, error };
}
