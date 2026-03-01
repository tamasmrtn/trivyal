import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { FindingStatus } from "@/lib/api/types";

const statusStyles: Record<FindingStatus, string> = {
  active: "bg-red-600 text-white border-red-600",
  fixed: "bg-green-600 text-white border-green-600",
  accepted: "bg-yellow-500 text-black border-yellow-500",
  false_positive: "bg-gray-500 text-white border-gray-500",
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
