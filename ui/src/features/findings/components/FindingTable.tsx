import { Link } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { FindingStatusBadge } from "./FindingStatusBadge";
import { AcceptRiskDialog } from "./AcceptRiskDialog";
import type { FindingResponse } from "@/lib/api/types";

interface FindingTableProps {
  findings: FindingResponse[];
  onAccepted: () => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function FindingTable({ findings, onAccepted }: FindingTableProps) {
  if (findings.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-lg border border-dashed">
        <p className="text-muted-foreground">
          No findings match the current filters.
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>CVE</TableHead>
          <TableHead>Package</TableHead>
          <TableHead>Installed</TableHead>
          <TableHead>Fixed</TableHead>
          <TableHead>Severity</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>First Seen</TableHead>
          <TableHead>Last Seen</TableHead>
          <TableHead className="w-[60px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {findings.map((finding) => (
          <TableRow key={finding.id}>
            <TableCell>
              <Link
                to={`/findings/${finding.id}`}
                className="font-mono text-xs hover:underline"
              >
                {finding.cve_id}
              </Link>
            </TableCell>
            <TableCell>{finding.package_name}</TableCell>
            <TableCell className="font-mono text-xs">
              {finding.installed_version}
            </TableCell>
            <TableCell className="font-mono text-xs">
              {finding.fixed_version ?? "—"}
            </TableCell>
            <TableCell>
              <SeverityBadge severity={finding.severity} />
            </TableCell>
            <TableCell>
              <FindingStatusBadge status={finding.status} />
            </TableCell>
            <TableCell>{formatDate(finding.first_seen)}</TableCell>
            <TableCell>{formatDate(finding.last_seen)}</TableCell>
            <TableCell>
              {finding.status === "active" && (
                <AcceptRiskDialog
                  findingId={finding.id}
                  cveId={finding.cve_id}
                  onAccepted={onAccepted}
                />
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
