import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Severity } from "@/lib/api/types";

const severityStyles: Record<Severity, string> = {
  CRITICAL: "bg-red-600/15 text-red-400 border border-red-600/30",
  HIGH: "bg-orange-600/15 text-orange-400 border border-orange-600/30",
  MEDIUM: "bg-amber-600/15 text-amber-400 border border-amber-600/30",
  LOW: "bg-blue-600/15 text-blue-400 border border-blue-600/30",
  UNKNOWN: "bg-gray-600/15 text-gray-400 border border-gray-600/30",
};

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <Badge className={cn(severityStyles[severity], className)}>
      {severity}
    </Badge>
  );
}
