import { useCallback, useEffect, useState } from "react";
import { fetchSettings } from "@/lib/api/settings";
import type { SettingsResponse } from "@/lib/api/types";

export function useSettings() {
  const [data, setData] = useState<SettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);

    fetchSettings()
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load settings",
          );
          setLoading(false);
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
