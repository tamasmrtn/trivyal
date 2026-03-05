import { useCallback, useEffect, useReducer } from "react";
import { fetchFindings } from "@/lib/api/findings";
import type { FindingResponse, FindingStatus, Severity } from "@/lib/api/types";

interface UseFindingsOptions {
  severity?: Severity;
  status?: FindingStatus;
  cve_id?: string;
  package?: string;
  container_id?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

type State = {
  data: FindingResponse[];
  total: number;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: FindingResponse[]; total: number }
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

export function useFindings(options?: UseFindingsOptions) {
  const severity = options?.severity;
  const status = options?.status;
  const cveId = options?.cve_id;
  const pkg = options?.package;
  const containerId = options?.container_id;
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

    fetchFindings({
      severity,
      status,
      cve_id: cveId,
      package: pkg,
      container_id: containerId,
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
              err instanceof Error ? err.message : "Failed to load findings",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    severity,
    status,
    cveId,
    pkg,
    containerId,
    sortBy,
    sortDir,
    page,
    pageSize,
  ]);

  useEffect(() => {
    return load();
  }, [load]);

  const refetch = useCallback(() => {
    load();
  }, [load]);

  return { data, total, loading, error, refetch };
}
