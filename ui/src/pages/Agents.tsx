import { AgentTable, AddAgentDialog, useAgents } from "@/features/agents";
import { deleteAgent } from "@/lib/api/agents";

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

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading agents...</p>
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
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Agents</h1>
        <AddAgentDialog onCreated={refetch} />
      </div>
      <AgentTable agents={data} onDelete={handleDelete} />
    </div>
  );
}
