import { Link } from "react-router-dom";
import { ChevronDown, ChevronUp, ChevronsUpDown } from "lucide-react";
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
  sortBy: string;
  sortDir: "asc" | "desc";
  onSort: (column: string) => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

function SortIcon({
  column,
  sortBy,
  sortDir,
}: {
  column: string;
  sortBy: string;
  sortDir: "asc" | "desc";
}) {
  if (sortBy !== column)
    return <ChevronsUpDown className="ml-1 inline h-3 w-3 opacity-40" />;
  return sortDir === "asc" ? (
    <ChevronUp className="ml-1 inline h-3 w-3" />
  ) : (
    <ChevronDown className="ml-1 inline h-3 w-3" />
  );
}

function SortableHead({
  column,
  label,
  sortBy,
  sortDir,
  onSort,
}: {
  column: string;
  label: string;
  sortBy: string;
  sortDir: "asc" | "desc";
  onSort: (col: string) => void;
}) {
  return (
    <TableHead>
      <button
        onClick={() => onSort(column)}
        className="hover:text-foreground flex items-center whitespace-nowrap"
      >
        {label}
        <SortIcon column={column} sortBy={sortBy} sortDir={sortDir} />
      </button>
    </TableHead>
  );
}

export function FindingTable({
  findings,
  onAccepted,
  sortBy,
  sortDir,
  onSort,
}: FindingTableProps) {
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
          <SortableHead
            column="cve_id"
            label="CVE"
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={onSort}
          />
          <SortableHead
            column="package_name"
            label="Package"
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={onSort}
          />
          <TableHead>Installed</TableHead>
          <TableHead>Fixed</TableHead>
          <SortableHead
            column="container"
            label="Container"
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={onSort}
          />
          <SortableHead
            column="severity"
            label="Severity"
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={onSort}
          />
          <SortableHead
            column="status"
            label="Status"
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={onSort}
          />
          <SortableHead
            column="first_seen"
            label="First Seen"
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={onSort}
          />
          <SortableHead
            column="last_seen"
            label="Last Seen"
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={onSort}
          />
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
            <TableCell className="font-mono text-xs">
              {finding.container_name ?? "—"}
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
