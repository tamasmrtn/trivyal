import { useCallback, useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  createPatch,
  subscribePatchLogs,
  triggerRestart,
} from "@/lib/api/patches";
import type { PatchResponse } from "@/lib/api/types";

interface PatchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  containerId: string;
  imageName: string;
}

export function PatchDialog({
  open,
  onOpenChange,
  agentId,
  containerId,
  imageName,
}: PatchDialogProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const [patchResult, setPatchResult] = useState<PatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [restarting, setRestarting] = useState(false);
  const [restartDone, setRestartDone] = useState(false);
  const [restartError, setRestartError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const startPatch = useCallback(async () => {
    setLogs([]);
    setPatchResult(null);
    setError(null);

    try {
      const patch = await createPatch({
        agent_id: agentId,
        container_id: containerId,
        image_name: imageName,
      });

      subscribePatchLogs(
        patch.id,
        (line) => {
          setLogs((prev) => [...prev, line]);
        },
        async () => {
          // Re-fetch the patch to get final status
          const { fetchPatch } = await import("@/lib/api/patches");
          try {
            const result = await fetchPatch(patch.id);
            setPatchResult(result);
          } catch {
            // Use the initial patch data as fallback
            setPatchResult(patch);
          }
        },
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create patch");
    }
  }, [agentId, containerId, imageName]);

  useEffect(() => {
    if (open) {
      startPatch();
    }
    return () => {
      setLogs([]);
      setPatchResult(null);
      setError(null);
      setRestarting(false);
      setRestartDone(false);
      setRestartError(null);
    };
  }, [open, startPatch]);

  // Auto-scroll logs
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  async function handleRestart() {
    if (!patchResult) return;
    setRestarting(true);
    setRestartError(null);
    try {
      const result = await triggerRestart(patchResult.id);
      if (result.status === "blocked") {
        setRestartError(
          result.block_reason ??
            "Restart blocked — container may have anonymous volumes",
        );
      } else {
        setRestartDone(true);
      }
    } catch (err: unknown) {
      setRestartError(
        err instanceof Error ? err.message : "Failed to restart container",
      );
    } finally {
      setRestarting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Patch {imageName}</DialogTitle>
        </DialogHeader>

        {error && <p className="text-destructive text-sm">{error}</p>}

        <div
          ref={logRef}
          className="max-h-64 overflow-y-auto rounded-md bg-zinc-950 p-3 font-mono text-xs text-zinc-300"
        >
          {logs.length === 0 && !patchResult && !error && (
            <p className="text-zinc-500">Waiting for Copa output...</p>
          )}
          {logs.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>

        {patchResult && (
          <div className="space-y-3">
            {patchResult.status === "completed" && (
              <>
                <p className="text-sm text-green-600 dark:text-green-400">
                  Image patched successfully
                  {patchResult.original_finding_count != null && (
                    <>
                      {" "}
                      — {patchResult.original_finding_count} fixable findings
                    </>
                  )}
                </p>
                {!restartDone && (
                  <Button
                    onClick={handleRestart}
                    disabled={restarting}
                    size="sm"
                  >
                    {restarting ? "Restarting..." : "Restart Container"}
                  </Button>
                )}
                {restartDone && (
                  <p className="text-sm text-green-600 dark:text-green-400">
                    Container restarted with patched image
                  </p>
                )}
                {restartError && (
                  <p className="text-destructive text-sm">{restartError}</p>
                )}
              </>
            )}
            {patchResult.status === "failed" && (
              <p className="text-destructive text-sm">
                Patch failed: {patchResult.error_message ?? "Unknown error"}
              </p>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
