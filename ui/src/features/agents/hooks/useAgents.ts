import { useCallback, useEffect, useReducer } from "react";
import { fetchAgents } from "@/lib/api/agents";
import type { AgentResponse, AgentStatus } from "@/lib/api/types";

interface UseAgentsOptions {
  status?: AgentStatus;
  page?: number;
  page_size?: number;
}

type State = {
  data: AgentResponse[];
  total: number;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: AgentResponse[]; total: number }
  | { type: "ERROR"; error: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "LOADING":
      return { ...state, loading: true, error: null };
    case "SUCCESS":
      return {
        data: action.data,
        total: action.total,
        loading: false,
        error: null,
      };
    case "ERROR":
      return { ...state, loading: false, error: action.error };
  }
}

export function useAgents(options?: UseAgentsOptions) {
  const status = options?.status;
  const page = options?.page;
  const pageSize = options?.page_size;

  const [{ data, total, loading, error }, dispatch] = useReducer(reducer, {
    data: [],
    total: 0,
    loading: true,
    error: null,
  });

  const load = useCallback(() => {
    let cancelled = false;
    dispatch({ type: "LOADING" });

    fetchAgents({ status, page, page_size: pageSize })
      .then((res) => {
        if (!cancelled) {
          dispatch({ type: "SUCCESS", data: res.data, total: res.total });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          dispatch({
            type: "ERROR",
            error: err instanceof Error ? err.message : "Failed to load agents",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [status, page, pageSize]);

  useEffect(() => {
    return load();
  }, [load]);

  const refetch = useCallback(() => {
    load();
  }, [load]);

  return { data, total, loading, error, refetch };
}
