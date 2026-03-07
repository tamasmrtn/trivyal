import { useCallback, useEffect, useReducer } from "react";
import { fetchMisconfigs } from "@/lib/api/misconfigs";
import type {
  MisconfigFindingResponse,
  MisconfigStatus,
  Severity,
} from "@/lib/api/types";

interface UseMisconfigsOptions {
  severity?: Severity;
  status?: MisconfigStatus;
  agent_id?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

type State = {
  data: MisconfigFindingResponse[];
  total: number;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: MisconfigFindingResponse[]; total: number }
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

export function useMisconfigs(options?: UseMisconfigsOptions) {
  const severity = options?.severity;
  const status = options?.status;
  const agentId = options?.agent_id;
  const sortBy = options?.sort_by;
  const sortDir = options?.sort_dir;
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

    fetchMisconfigs({
      severity,
      status,
      agent_id: agentId,
      sort_by: sortBy,
      sort_dir: sortDir,
      page,
      page_size: pageSize,
    })
      .then((res) => {
        if (!cancelled) {
          dispatch({ type: "SUCCESS", data: res.data, total: res.total });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          dispatch({
            type: "ERROR",
            error:
              err instanceof Error
                ? err.message
                : "Failed to load misconfigurations",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [severity, status, agentId, sortBy, sortDir, page, pageSize]);

  useEffect(() => {
    return load();
  }, [load]);

  const refetch = useCallback(() => {
    load();
  }, [load]);

  return { data, total, loading, error, refetch };
}
