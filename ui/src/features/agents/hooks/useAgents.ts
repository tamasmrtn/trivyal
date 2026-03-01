import { useCallback, useEffect, useState } from "react";
import { fetchAgents } from "@/lib/api/agents";
import type { AgentResponse, AgentStatus } from "@/lib/api/types";

interface UseAgentsOptions {
  status?: AgentStatus;
  page?: number;
  page_size?: number;
}

export function useAgents(options?: UseAgentsOptions) {
  const status = options?.status;
  const page = options?.page;
  const pageSize = options?.page_size;

  const [data, setData] = useState<AgentResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);

    fetchAgents({ status, page, page_size: pageSize })
      .then((res) => {
        if (!cancelled) {
          setData(res.data);
          setTotal(res.total);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load agents",
          );
          setLoading(false);
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
