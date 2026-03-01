import { useCallback, useEffect, useState } from "react";
import {
  fetchFinding,
  fetchAcceptances,
  type RiskAcceptanceResponse,
} from "@/lib/api/findings";
import type { FindingResponse } from "@/lib/api/types";

export function useFinding(id: string) {
  const [finding, setFinding] = useState<FindingResponse | null>(null);
  const [acceptances, setAcceptances] = useState<RiskAcceptanceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);

    Promise.all([fetchFinding(id), fetchAcceptances(id)])
      .then(([f, accs]) => {
        if (!cancelled) {
          setFinding(f);
          setAcceptances(accs);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load finding",
          );
          setLoading(false);
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
