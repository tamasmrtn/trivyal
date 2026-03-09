import { useEffect, useReducer } from "react";
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

type State = {
  data: InsightsData | null;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: InsightsData }
  | { type: "ERROR"; error: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "LOADING":
      return { data: state.data, loading: true, error: null };
    case "SUCCESS":
      return { data: action.data, loading: false, error: null };
    case "ERROR":
      return { ...state, loading: false, error: action.error };
  }
}

export function useInsights(
  window: number,
  fixable?: boolean,
  agentId?: string,
) {
  const [{ data, loading, error }, dispatch] = useReducer(reducer, {
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    dispatch({ type: "LOADING" });

    Promise.all([
      fetchInsightsSummary(window, fixable, agentId),
      fetchInsightsTrend(window, fixable, agentId),
      fetchAgentsTrend(window, fixable, agentId),
      fetchTopCves(window, fixable, agentId),
    ])
      .then(([summary, trend, agentsTrend, topCves]) => {
        if (!cancelled) {
          dispatch({
            type: "SUCCESS",
            data: { summary, trend, agentsTrend, topCves },
          });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          dispatch({
            type: "ERROR",
            error:
              err instanceof Error ? err.message : "Failed to load insights",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [window, fixable, agentId]);

  return { data, loading, error };
}
