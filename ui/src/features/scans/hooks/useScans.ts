import { useCallback, useEffect, useState } from "react";
import { fetchScans, fetchAgentScans } from "@/lib/api/scans";
import type { ScanResultResponse } from "@/lib/api/types";

interface UseScansOptions {
  agentId?: string;
  page?: number;
  page_size?: number;
}

export function useScans(options?: UseScansOptions) {
  const agentId = options?.agentId;
  const page = options?.page;
  const pageSize = options?.page_size;

  const [data, setData] = useState<ScanResultResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);

    const request = agentId
      ? fetchAgentScans(agentId, { page, page_size: pageSize })
      : fetchScans({ page, page_size: pageSize });

    request
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
            err instanceof Error ? err.message : "Failed to load scan history",
          );
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [agentId, page, pageSize]);

  useEffect(() => {
    return load();
  }, [load]);

  const refetch = useCallback(() => {
    load();
  }, [load]);

  return { data, total, loading, error, refetch };
}
