import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createAcceptance } from "@/lib/api/findings";
import { ShieldCheck } from "lucide-react";

interface AcceptRiskDialogProps {
  findingId: string;
  cveId: string;
  onAccepted: () => void;
}

export function AcceptRiskDialog({
  findingId,
  cveId,
  onAccepted,
}: AcceptRiskDialogProps) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setReason("");
    setExpiresAt("");
    setSubmitting(false);
    setError(null);
  }

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (!next) reset();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reason.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      await createAcceptance(findingId, reason.trim(), expiresAt || null);
      setOpen(false);
      reset();
      onAccepted();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to accept risk");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Accept risk for ${cveId}`}
        >
          <ShieldCheck className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Accept Risk</DialogTitle>
            <DialogDescription>
              Accept the risk for {cveId}. This will mark the finding as
              accepted.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label
                htmlFor="acceptance-reason"
                className="mb-2 block text-sm font-medium"
              >
                Reason
              </label>
              <Input
                id="acceptance-reason"
                placeholder="e.g. Not exploitable in our environment"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                disabled={submitting}
                autoFocus
              />
            </div>
            <div>
              <label
                htmlFor="acceptance-expires"
                className="mb-2 block text-sm font-medium"
              >
                Expires at (optional)
              </label>
              <Input
                id="acceptance-expires"
                type="date"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                disabled={submitting}
              />
            </div>
            {error && (
              <p className="text-destructive-foreground text-sm">{error}</p>
            )}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={submitting || !reason.trim()}>
              {submitting ? "Accepting..." : "Accept Risk"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
