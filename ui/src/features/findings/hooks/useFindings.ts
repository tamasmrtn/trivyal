import { useCallback, useEffect, useState } from "react";
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

  const [data, setData] = useState<FindingResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);

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
          setData(res.data);
          setTotal(res.total);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load findings",
          );
          setLoading(false);
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
