import { useCallback, useEffect, useReducer } from "react";
import {
  fetchFinding,
  fetchAcceptances,
  type RiskAcceptanceResponse,
} from "@/lib/api/findings";
import type { FindingResponse } from "@/lib/api/types";

type State = {
  finding: FindingResponse | null;
  acceptances: RiskAcceptanceResponse[];
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | {
      type: "SUCCESS";
      finding: FindingResponse;
      acceptances: RiskAcceptanceResponse[];
    }
  | { type: "ERROR"; error: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "LOADING":
      return { ...state, loading: true, error: null };
    case "SUCCESS":
      return {
        finding: action.finding,
        acceptances: action.acceptances,
        loading: false,
        error: null,
      };
    case "ERROR":
      return { ...state, loading: false, error: action.error };
  }
}

export function useFinding(id: string) {
  const [{ finding, acceptances, loading, error }, dispatch] = useReducer(
    reducer,
    {
      finding: null,
      acceptances: [],
      loading: true,
      error: null,
    },
  );

  const load = useCallback(() => {
    let cancelled = false;
    dispatch({ type: "LOADING" });

    Promise.all([fetchFinding(id), fetchAcceptances(id)])
      .then(([f, accs]) => {
        if (!cancelled) {
          dispatch({ type: "SUCCESS", finding: f, acceptances: accs });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          dispatch({
            type: "ERROR",
            error:
              err instanceof Error ? err.message : "Failed to load finding",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    return load();
  }, [load]);

  const refetch = useCallback(() => {
    load();
  }, [load]);

  return { finding, acceptances, loading, error, refetch };
}
