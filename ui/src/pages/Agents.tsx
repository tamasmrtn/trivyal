import { AgentTable, AddAgentDialog, useAgents } from "@/features/agents";
import { deleteAgent } from "@/lib/api/agents";
import { triggerScan } from "@/lib/api/scans";
import { Skeleton } from "@/components/ui/skeleton";

export function Agents() {
  const { data, loading, error, refetch } = useAgents();

  async function handleDelete(id: string) {
    try {
      await deleteAgent(id);
      refetch();
    } catch {
      // Silently fail — the agent remains in the list
    }
  }

  async function handleTriggerScan(id: string) {
    try {
      await triggerScan(id);
    } catch {
      // Best-effort — agent may not be connected
    }
  }

  if (loading) {
    return (
      <div>
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-9 w-28" />
        </div>
        <div className="overflow-hidden rounded-lg border">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex gap-4 border-b px-4 py-3 last:border-0"
            >
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-24" />
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
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Agents</h1>
        <AddAgentDialog onCreated={refetch} />
      </div>
      <AgentTable
        agents={data}
        onDelete={handleDelete}
        onTriggerScan={handleTriggerScan}
      />
    </div>
  );
}
