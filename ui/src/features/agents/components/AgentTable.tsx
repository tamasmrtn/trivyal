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
import { Trash2 } from "lucide-react";

interface AgentTableProps {
  agents: AgentResponse[];
  onDelete: (id: string) => void;
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

export function AgentTable({ agents, onDelete }: AgentTableProps) {
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
          <TableHead>Hostname</TableHead>
          <TableHead>Last Seen</TableHead>
          <TableHead>Created</TableHead>
          <TableHead className="w-[60px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {agents.map((agent) => (
          <TableRow key={agent.id}>
            <TableCell className="font-medium">{agent.name}</TableCell>
            <TableCell>
              <StatusBadge status={agent.status} />
            </TableCell>
            <TableCell>{formatHostname(agent.host_metadata)}</TableCell>
            <TableCell>{formatLastSeen(agent.last_seen)}</TableCell>
            <TableCell>
              {new Date(agent.created_at).toLocaleDateString()}
            </TableCell>
            <TableCell>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onDelete(agent.id)}
                aria-label={`Delete ${agent.name}`}
              >
                <Trash2 className="text-destructive-foreground h-4 w-4" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
