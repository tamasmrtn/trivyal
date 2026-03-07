import { useEffect, useReducer } from "react";
import { fetchDashboardSummary } from "@/lib/api/dashboard";
import type { DashboardSummary } from "@/lib/api/types";

type State = {
  data: DashboardSummary | null;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: DashboardSummary }
  | { type: "ERROR"; error: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "LOADING":
      return { ...state, loading: true, error: null };
    case "SUCCESS":
      return { data: action.data, loading: false, error: null };
    case "ERROR":
      return { ...state, loading: false, error: action.error };
  }
}

export function useDashboard(fixable?: boolean) {
  const [{ data, loading, error }, dispatch] = useReducer(reducer, {
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    dispatch({ type: "LOADING" });

    fetchDashboardSummary(fixable)
      .then((summary) => {
        if (!cancelled) dispatch({ type: "SUCCESS", data: summary });
      })
      .catch((err: unknown) => {
        if (!cancelled)
          dispatch({
            type: "ERROR",
            error:
              err instanceof Error ? err.message : "Failed to load dashboard",
          });
      });

    return () => {
      cancelled = true;
    };
  }, [fixable]);

  return { data, loading, error };
}
