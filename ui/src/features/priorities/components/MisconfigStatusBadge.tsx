import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { MisconfigStatus } from "@/lib/api/types";

const statusStyles: Record<MisconfigStatus, string> = {
  active: "bg-sky-600/15 text-sky-400 border border-sky-600/30",
  fixed: "bg-green-700/15 text-green-400 border border-green-700/30",
  accepted: "bg-violet-600/15 text-violet-400 border border-violet-600/30",
  false_positive: "bg-gray-600/15 text-gray-400 border border-gray-600/30",
};

const statusLabels: Record<MisconfigStatus, string> = {
  active: "Active",
  fixed: "Fixed",
  accepted: "Accepted",
  false_positive: "False Positive",
};

interface MisconfigStatusBadgeProps {
  status: MisconfigStatus;
  className?: string;
}

export function MisconfigStatusBadge({
  status,
  className,
}: MisconfigStatusBadgeProps) {
  return (
    <Badge className={cn(statusStyles[status], className)}>
      {statusLabels[status]}
    </Badge>
  );
}
