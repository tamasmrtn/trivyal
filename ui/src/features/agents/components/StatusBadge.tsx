import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AgentStatus } from "@/lib/api/types";

const statusStyles: Record<AgentStatus, string> = {
  online: "bg-green-600/15 text-green-400 border border-green-600/30",
  offline: "bg-red-600/15 text-red-400 border border-red-600/30",
  scanning: "bg-primary/15 text-primary border border-primary/30",
};

const statusLabels: Record<AgentStatus, string> = {
  online: "Online",
  offline: "Offline",
  scanning: "Scanning",
};

interface StatusBadgeProps {
  status: AgentStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <Badge className={cn(statusStyles[status], className)}>
      {statusLabels[status]}
    </Badge>
  );
}
