import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AgentStatus } from "@/lib/api/types";

const statusStyles: Record<AgentStatus, string> = {
  online: "bg-green-600 text-white border-green-600",
  offline: "bg-red-600 text-white border-red-600",
  scanning: "bg-blue-600 text-white border-blue-600",
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
