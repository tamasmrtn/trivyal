import { useCallback, useEffect, useReducer } from "react";
import { fetchImages } from "@/lib/api/images";
import type { ImageResponse } from "@/lib/api/types";

interface UseImagesOptions {
  agent_id?: string;
  fixable?: boolean;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

type State = {
  data: ImageResponse[];
  total: number;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: ImageResponse[]; total: number }
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

export function useImages(options?: UseImagesOptions) {
  const agentId = options?.agent_id;
  const fixable = options?.fixable;
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

    fetchImages({
      agent_id: agentId,
      fixable,
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
            error: err instanceof Error ? err.message : "Failed to load images",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [agentId, fixable, sortBy, sortDir, page, pageSize]);

  useEffect(() => {
    return load();
  }, [load]);

  return { data, total, loading, error };
}
