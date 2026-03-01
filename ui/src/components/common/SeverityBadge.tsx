import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Severity } from "@/lib/api/types";

const severityStyles: Record<Severity, string> = {
  CRITICAL: "bg-red-600 text-white border-red-600",
  HIGH: "bg-orange-500 text-white border-orange-500",
  MEDIUM: "bg-yellow-500 text-black border-yellow-500",
  LOW: "bg-blue-500 text-white border-blue-500",
  UNKNOWN: "bg-gray-500 text-white border-gray-500",
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
