import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Severity } from "@/lib/api/types";

const severityStyles: Record<Severity, string> = {
  CRITICAL: "bg-red-600 text-white border-transparent",
  HIGH: "bg-orange-600 text-white border-transparent",
  MEDIUM: "bg-amber-600 text-black border-transparent",
  LOW: "bg-blue-600 text-white border-transparent",
  UNKNOWN: "bg-gray-600 text-white border-transparent",
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
