import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { ScanTable, useScans } from "@/features/scans";
import { useAgents } from "@/features/agents";
import { Button } from "@/components/ui/button";
import { triggerScan } from "@/lib/api/scans";

export function ScanHistory() {
  const [agentId, setAgentId] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [triggering, setTriggering] = useState(false);

  const { data: agents } = useAgents({ page_size: 200 });
  const { data, total, loading, error } = useScans({
    agentId,
    page,
    page_size: 50,
  });

  const totalPages = Math.max(1, Math.ceil(total / 50));

  function handleAgentChange(value: string) {
    setAgentId(value || undefined);
    setPage(1);
  }

  async function handleTriggerScan() {
    if (!agentId) return;
    setTriggering(true);
    try {
      await triggerScan(agentId);
    } catch {
      // Best-effort — agent may not be connected
    } finally {
      setTriggering(false);
    }
  }

  if (loading) {
    return (
      <div>
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-9 w-36" />
        </div>
        <div className="overflow-hidden rounded-lg border">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="flex gap-4 border-b px-4 py-3 last:border-0"
            >
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-28" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-destructive-foreground">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Scan History</h1>
        <div className="flex items-center gap-3">
          <select
            value={agentId ?? ""}
            onChange={(e) => handleAgentChange(e.target.value)}
            aria-label="Filter by agent"
            className="bg-input text-foreground focus:ring-ring rounded-md border px-3 py-2 text-sm focus:ring-2 focus:outline-none"
          >
            <option value="">All Agents</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
          {agentId && (
            <Button
              variant="outline"
              size="sm"
              disabled={triggering}
              onClick={handleTriggerScan}
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${triggering ? "animate-spin" : ""}`}
              />
              Trigger Scan
            </Button>
          )}
        </div>
      </div>

      <ScanTable scans={data} />

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-muted-foreground text-sm">
            {total} scan{total !== 1 ? "s" : ""} total
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="text-foreground hover:bg-accent hover:text-accent-foreground rounded-md border px-3 py-1 text-sm transition-colors disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-muted-foreground px-2 py-1 text-sm">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="text-foreground hover:bg-accent hover:text-accent-foreground rounded-md border px-3 py-1 text-sm transition-colors disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
