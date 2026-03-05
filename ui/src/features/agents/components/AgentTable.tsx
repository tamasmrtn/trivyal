import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "./StatusBadge";
import type { AgentResponse } from "@/lib/api/types";
import { RefreshCw, Trash2 } from "lucide-react";

interface AgentTableProps {
  agents: AgentResponse[];
  onDelete: (id: string) => void;
  onTriggerScan: (id: string) => Promise<void>;
}

function formatLastSeen(lastSeen: string | null): string {
  if (!lastSeen) return "Never";
  const date = new Date(lastSeen);
  return date.toLocaleString();
}

function formatHostname(metadata: Record<string, unknown> | null): string {
  if (!metadata?.hostname) return "-";
  return String(metadata.hostname);
}

export function AgentTable({
  agents,
  onDelete,
  onTriggerScan,
}: AgentTableProps) {
  const [scanning, setScanning] = useState<Set<string>>(new Set());

  async function handleTriggerScan(id: string) {
    setScanning((prev) => new Set(prev).add(id));
    try {
      await onTriggerScan(id);
    } finally {
      setScanning((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }

  if (agents.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-lg border border-dashed">
        <p className="text-muted-foreground">
          No agents registered yet. Add one to get started.
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="hidden sm:table-cell">Hostname</TableHead>
          <TableHead className="hidden sm:table-cell">Last Seen</TableHead>
          <TableHead className="hidden sm:table-cell">Created</TableHead>
          <TableHead className="w-[100px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {agents.map((agent) => (
          <TableRow key={agent.id}>
            <TableCell className="font-medium">{agent.name}</TableCell>
            <TableCell>
              <StatusBadge status={agent.status} />
            </TableCell>
            <TableCell className="hidden sm:table-cell">
              {formatHostname(agent.host_metadata)}
            </TableCell>
            <TableCell className="hidden sm:table-cell">
              {formatLastSeen(agent.last_seen)}
            </TableCell>
            <TableCell className="hidden sm:table-cell">
              {new Date(agent.created_at).toLocaleDateString()}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  disabled={agent.status !== "online" || scanning.has(agent.id)}
                  onClick={() => handleTriggerScan(agent.id)}
                  aria-label={`Scan ${agent.name}`}
                >
                  <RefreshCw
                    className={`h-4 w-4 ${scanning.has(agent.id) ? "animate-spin" : ""}`}
                  />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onDelete(agent.id)}
                  aria-label={`Delete ${agent.name}`}
                >
                  <Trash2 className="text-destructive-foreground h-4 w-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
