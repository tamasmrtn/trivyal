import { useCallback, useEffect, useReducer } from "react";
import { fetchPatches } from "@/lib/api/patches";
import type { PatchResponse, PatchStatus } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Wrench } from "lucide-react";
import { cn } from "@/lib/utils";

type State = {
  data: PatchResponse[];
  total: number;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: "LOADING" }
  | { type: "SUCCESS"; data: PatchResponse[]; total: number }
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

const statusStyles: Record<PatchStatus, string> = {
  pending: "bg-muted text-muted-foreground",
  running: "bg-blue-500/15 text-blue-700 dark:text-blue-400",
  completed: "bg-green-500/15 text-green-700 dark:text-green-400",
  failed: "bg-destructive/15 text-destructive",
};

function StatusBadge({ status }: { status: PatchStatus }) {
  return (
    <Badge variant="outline" className={cn("capitalize", statusStyles[status])}>
      {status}
    </Badge>
  );
}

export function Patches() {
  const [{ data, total, loading, error }, dispatch] = useReducer(reducer, {
    data: [],
    total: 0,
    loading: true,
    error: null,
  });

  const load = useCallback(() => {
    dispatch({ type: "LOADING" });
    fetchPatches({ page_size: 100 })
      .then((res) =>
        dispatch({ type: "SUCCESS", data: res.data, total: res.total }),
      )
      .catch((err: unknown) =>
        dispatch({
          type: "ERROR",
          error: err instanceof Error ? err.message : "Failed to load patches",
        }),
      );
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Patches</h1>
        <p className="text-muted-foreground text-sm">
          Copa patch history across your infrastructure
        </p>
      </div>

      {loading && (
        <div className="flex h-32 items-center justify-center">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      )}

      {error && (
        <div className="flex h-32 items-center justify-center">
          <p className="text-destructive-foreground">{error}</p>
        </div>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed">
          <Wrench className="text-muted-foreground h-5 w-5" />
          <p className="text-muted-foreground text-sm">No patches yet</p>
        </div>
      )}

      {!loading && !error && data.length > 0 && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Image
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Status
                </TableHead>
                <TableHead className="text-muted-foreground hidden text-xs tracking-wide uppercase sm:table-cell">
                  Findings
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  When
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((patch) => (
                <TableRow key={patch.id}>
                  <TableCell
                    className="max-w-[200px] truncate text-sm"
                    title={patch.image_name}
                  >
                    {patch.image_name}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={patch.status} />
                  </TableCell>
                  <TableCell className="hidden sm:table-cell">
                    {patch.original_finding_count != null ? (
                      <span className="text-sm">
                        {patch.original_finding_count}
                        {patch.patched_finding_count != null && (
                          <span className="text-muted-foreground">
                            {" "}
                            → {patch.patched_finding_count}
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(patch.requested_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <p className="text-muted-foreground text-sm">
            {total} patch{total !== 1 ? "es" : ""}
          </p>
        </>
      )}
    </div>
  );
}
