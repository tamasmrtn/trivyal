import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { FindingStatus } from "@/lib/api/types";

const statusStyles: Record<FindingStatus, string> = {
  active: "bg-red-600 text-white border-transparent",
  fixed: "bg-green-600 text-white border-transparent",
  accepted: "bg-amber-600 text-white border-transparent",
  false_positive: "bg-gray-600 text-white border-transparent",
};

const statusLabels: Record<FindingStatus, string> = {
  active: "Active",
  fixed: "Fixed",
  accepted: "Accepted",
  false_positive: "False Positive",
};

interface FindingStatusBadgeProps {
  status: FindingStatus;
  className?: string;
}

export function FindingStatusBadge({
  status,
  className,
}: FindingStatusBadgeProps) {
  return (
    <Badge className={cn(statusStyles[status], className)}>
      {statusLabels[status]}
    </Badge>
  );
}
