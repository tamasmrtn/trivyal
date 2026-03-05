import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ShieldCheck, ShieldOff } from "lucide-react";
import { useFinding } from "@/features/findings";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { FindingStatusBadge, AcceptRiskDialog } from "@/features/findings";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { updateFinding, revokeAcceptance } from "@/lib/api/findings";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function FindingDetail() {
  const { id } = useParams<{ id: string }>();
  const { finding, acceptances, loading, error, refetch } = useFinding(id!);
  const [statusChanging, setStatusChanging] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  async function handleStatusChange(newStatus: "active" | "false_positive") {
    if (!finding) return;
    setStatusChanging(true);
    setStatusError(null);
    try {
      await updateFinding(finding.id, newStatus);
      refetch();
    } catch (err: unknown) {
      setStatusError(
        err instanceof Error ? err.message : "Failed to update status",
      );
    } finally {
      setStatusChanging(false);
    }
  }

  async function handleRevoke(acceptanceId: string) {
    if (!finding) return;
    try {
      await revokeAcceptance(finding.id, acceptanceId);
      refetch();
    } catch {
      // revoke errors are silent; the list will simply not update
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (error || !finding) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-destructive-foreground">
          {error ?? "Finding not found"}
        </p>
      </div>
    );
  }

  const canAccept = finding.status === "active";
  const canMarkFalsePositive = finding.status === "active";
  const canMarkActive = finding.status === "false_positive";
  const showActions = canAccept || canMarkFalsePositive || canMarkActive;

  return (
    <div className="space-y-6">
      <Link
        to="/findings"
        className="text-muted-foreground hover:text-foreground inline-flex items-center gap-1 text-sm"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Findings
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 className="font-mono text-2xl font-bold">{finding.cve_id}</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            {finding.package_name} &middot; {finding.installed_version}
            {finding.fixed_version && ` → ${finding.fixed_version}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <FindingStatusBadge status={finding.status} />
        </div>
      </div>

      {/* Details */}
      <div className="rounded-lg border">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">Details</h2>
        </div>
        <dl className="divide-y text-sm">
          {finding.description && (
            <div className="flex px-4 py-3">
              <dt className="text-muted-foreground w-40 shrink-0">
                Description
              </dt>
              <dd className="leading-relaxed">{finding.description}</dd>
            </div>
          )}
          <div className="flex px-4 py-3">
            <dt className="text-muted-foreground w-40 shrink-0">Package</dt>
            <dd className="font-medium">{finding.package_name}</dd>
          </div>
          <div className="flex px-4 py-3">
            <dt className="text-muted-foreground w-40 shrink-0">
              Installed version
            </dt>
            <dd className="font-mono text-xs">{finding.installed_version}</dd>
          </div>
          <div className="flex px-4 py-3">
            <dt className="text-muted-foreground w-40 shrink-0">Fixed in</dt>
            <dd className="font-mono text-xs">
              {finding.fixed_version ?? "—"}
            </dd>
          </div>
          <div className="flex px-4 py-3">
            <dt className="text-muted-foreground w-40 shrink-0">First seen</dt>
            <dd>{formatDate(finding.first_seen)}</dd>
          </div>
          <div className="flex px-4 py-3">
            <dt className="text-muted-foreground w-40 shrink-0">Last seen</dt>
            <dd>{formatDate(finding.last_seen)}</dd>
          </div>
          {finding.container_name && (
            <div className="flex px-4 py-3">
              <dt className="text-muted-foreground w-40 shrink-0">Container</dt>
              <dd className="font-mono text-xs">{finding.container_name}</dd>
            </div>
          )}
          <div className="flex px-4 py-3">
            <dt className="text-muted-foreground w-40 shrink-0">Scan result</dt>
            <dd className="font-mono text-xs">{finding.scan_result_id}</dd>
          </div>
        </dl>
      </div>

      {/* Actions */}
      {showActions && (
        <div className="rounded-lg border">
          <div className="border-b px-4 py-3">
            <h2 className="text-sm font-semibold">Actions</h2>
          </div>
          <div className="flex flex-wrap items-center gap-2 px-4 py-3">
            {canAccept && (
              <AcceptRiskDialog
                findingId={finding.id}
                cveId={finding.cve_id}
                onAccepted={refetch}
                trigger={
                  <Button variant="outline" size="sm">
                    <ShieldCheck className="mr-2 h-4 w-4" />
                    Accept Risk
                  </Button>
                }
              />
            )}
            {canMarkFalsePositive && (
              <Button
                variant="outline"
                size="sm"
                disabled={statusChanging}
                onClick={() => handleStatusChange("false_positive")}
              >
                Mark as False Positive
              </Button>
            )}
            {canMarkActive && (
              <Button
                variant="outline"
                size="sm"
                disabled={statusChanging}
                onClick={() => handleStatusChange("active")}
              >
                Mark as Active
              </Button>
            )}
            {statusError && (
              <p className="text-destructive-foreground text-sm">
                {statusError}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Risk Acceptances */}
      <div className="rounded-lg border">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">Risk Acceptances</h2>
        </div>
        {acceptances.length === 0 ? (
          <div className="flex h-20 items-center justify-center">
            <p className="text-muted-foreground text-sm">
              No risk acceptances recorded.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reason</TableHead>
                <TableHead className="hidden sm:table-cell">
                  Accepted By
                </TableHead>
                <TableHead>Expires At</TableHead>
                <TableHead className="hidden sm:table-cell">
                  Created At
                </TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {acceptances.map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{a.reason}</TableCell>
                  <TableCell className="hidden sm:table-cell">
                    {a.accepted_by}
                  </TableCell>
                  <TableCell>
                    {a.expires_at ? formatDate(a.expires_at) : "—"}
                  </TableCell>
                  <TableCell className="hidden sm:table-cell">
                    {formatDate(a.created_at)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label="Revoke acceptance"
                      onClick={() => handleRevoke(a.id)}
                    >
                      <ShieldOff className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
