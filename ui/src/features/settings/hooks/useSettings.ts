import { useCallback, useEffect, useReducer } from "react";
import { fetchSettings } from "@/lib/api/settings";
import type { SettingsResponse } from "@/lib/api/types";

type State = {
  data: SettingsResponse | null;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: SettingsResponse }
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

export function useSettings() {
  const [{ data, loading, error }, dispatch] = useReducer(reducer, {
    data: null,
    loading: true,
    error: null,
  });

  const load = useCallback(() => {
    let cancelled = false;
    dispatch({ type: "LOADING" });

    fetchSettings()
      .then((res) => {
        if (!cancelled) {
          dispatch({ type: "SUCCESS", data: res });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          dispatch({
            type: "ERROR",
            error:
              err instanceof Error ? err.message : "Failed to load settings",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return load();
  }, [load]);

  const refetch = useCallback(() => {
    load();
  }, [load]);

  return { data, loading, error, refetch };
}
