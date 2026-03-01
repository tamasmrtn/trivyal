import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AgentStatus } from "@/lib/api/types";

const statusStyles: Record<AgentStatus, string> = {
  online: "bg-green-600 text-white border-transparent",
  offline: "bg-red-600 text-white border-transparent",
  scanning: "bg-primary text-primary-foreground border-transparent",
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
