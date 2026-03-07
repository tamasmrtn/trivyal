import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { MisconfigStatusBadge } from "./MisconfigStatusBadge";
import {
  createMisconfigAcceptance,
  updateMisconfig,
} from "@/lib/api/misconfigs";
import type { MisconfigFindingResponse } from "@/lib/api/types";

interface MisconfigDetailDialogProps {
  finding: MisconfigFindingResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated: () => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function MisconfigDetailDialog({
  finding,
  open,
  onOpenChange,
  onUpdated,
}: MisconfigDetailDialogProps) {
  const [loading, setLoading] = useState(false);

  if (!finding) return null;

  async function handleAcceptRisk() {
    if (!finding) return;
    setLoading(true);
    try {
      await createMisconfigAcceptance(finding.id, "Accepted via Priorities");
      onUpdated();
      onOpenChange(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleFalsePositive() {
    if (!finding) return;
    setLoading(true);
    try {
      await updateMisconfig(finding.id, "false_positive");
      onUpdated();
      onOpenChange(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{finding.title}</DialogTitle>
          <DialogDescription>{finding.check_id}</DialogDescription>
        </DialogHeader>

        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-2">
            <SeverityBadge severity={finding.severity} />
            <MisconfigStatusBadge status={finding.status} />
          </div>

          <div className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
            <span className="text-muted-foreground">Container</span>
            <span>{finding.container_name ?? "—"}</span>
            <span className="text-muted-foreground">Image</span>
            <span>{finding.image_name ?? "—"}</span>
            <span className="text-muted-foreground">First Seen</span>
            <span>{formatDate(finding.first_seen)}</span>
            <span className="text-muted-foreground">Last Seen</span>
            <span>{formatDate(finding.last_seen)}</span>
          </div>

          <div>
            <p className="text-muted-foreground mb-1">Fix Guideline</p>
            <p className="bg-muted rounded-md p-3 text-sm">
              {finding.fix_guideline}
            </p>
          </div>
        </div>

        {finding.status === "active" && (
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="secondary"
              onClick={handleFalsePositive}
              disabled={loading}
            >
              Mark False Positive
            </Button>
            <Button
              variant="secondary"
              onClick={handleAcceptRisk}
              disabled={loading}
            >
              Accept Risk
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
