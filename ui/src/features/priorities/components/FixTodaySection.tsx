import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { MisconfigStatusBadge } from "./MisconfigStatusBadge";
import { MisconfigDetailDialog } from "./MisconfigDetailDialog";
import { useMisconfigs } from "../hooks/useMisconfigs";
import type {
  MisconfigFindingResponse,
  MisconfigStatus,
  Severity,
} from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const SEVERITY_OPTIONS: { value: Severity | undefined; label: string }[] = [
  { value: undefined, label: "All" },
  { value: "HIGH", label: "High" },
  { value: "MEDIUM", label: "Medium" },
];

const STATUS_OPTIONS: { value: MisconfigStatus | undefined; label: string }[] =
  [
    { value: undefined, label: "All" },
    { value: "active", label: "Active" },
    { value: "accepted", label: "Accepted" },
    { value: "false_positive", label: "False Positive" },
  ];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

export function FixTodaySection() {
  const [severity, setSeverity] = useState<Severity | undefined>();
  const [status, setStatus] = useState<MisconfigStatus | undefined>();
  const [selected, setSelected] = useState<MisconfigFindingResponse | null>(
    null,
  );

  const { data, total, loading, error, refetch } = useMisconfigs({
    severity,
    status,
    sort_by: "severity",
    sort_dir: "desc",
    page_size: 100,
  });

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Fix Today</h2>
        <p className="text-muted-foreground text-sm">
          Configuration issues in running containers
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-1 rounded-md border p-1">
          {SEVERITY_OPTIONS.map(({ value, label }) => (
            <Button
              key={label}
              variant="ghost"
              size="sm"
              onClick={() => setSeverity(value)}
              className={cn(
                severity === value && "bg-accent text-accent-foreground",
              )}
            >
              {label}
            </Button>
          ))}
        </div>
        <select
          value={status ?? ""}
          onChange={(e) =>
            setStatus(
              (e.target.value || undefined) as MisconfigStatus | undefined,
            )
          }
          aria-label="Filter by status"
          className="bg-input text-foreground focus:ring-ring rounded-md border px-3 py-2 text-sm focus:ring-2 focus:outline-none"
        >
          {STATUS_OPTIONS.map(({ value, label }) => (
            <option key={label} value={value ?? ""}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="flex h-32 items-center justify-center">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      )}

      {error && (
        <div className="flex h-32 items-center justify-center">
          <p className="text-destructive-foreground">{error}</p>
        </div>
      )}

      {!loading && !error && data.length === 0 && (
        <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed">
          <ShieldCheck className="text-muted-foreground h-5 w-5" />
          <p className="text-muted-foreground text-sm">
            No configuration issues found.
          </p>
        </div>
      )}

      {!loading && !error && data.length > 0 && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Severity
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Container
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Issue
                </TableHead>
                <TableHead className="text-muted-foreground hidden text-xs tracking-wide uppercase sm:table-cell">
                  Check ID
                </TableHead>
                <TableHead className="text-muted-foreground hidden text-xs tracking-wide uppercase md:table-cell">
                  Fix
                </TableHead>
                <TableHead className="text-muted-foreground hidden text-xs tracking-wide uppercase sm:table-cell">
                  First Seen
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Status
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((finding) => (
                <TableRow
                  key={finding.id}
                  onClick={() => setSelected(finding)}
                  className="hover:bg-accent/50 cursor-pointer"
                >
                  <TableCell>
                    <SeverityBadge severity={finding.severity} />
                  </TableCell>
                  <TableCell className="max-w-[120px] truncate text-sm">
                    {finding.container_name ?? "—"}
                  </TableCell>
                  <TableCell className="max-w-[160px] truncate text-sm">
                    {finding.title}
                  </TableCell>
                  <TableCell className="hidden font-mono text-xs sm:table-cell">
                    {finding.check_id}
                  </TableCell>
                  <TableCell className="text-muted-foreground hidden max-w-[200px] truncate text-xs md:table-cell">
                    {finding.fix_guideline}
                  </TableCell>
                  <TableCell className="text-muted-foreground hidden text-xs sm:table-cell">
                    {formatDate(finding.first_seen)}
                  </TableCell>
                  <TableCell>
                    <MisconfigStatusBadge status={finding.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <p className="text-muted-foreground text-sm">
            {total} issue{total !== 1 ? "s" : ""}
          </p>
        </>
      )}

      <MisconfigDetailDialog
        finding={selected}
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
        onUpdated={refetch}
      />
    </section>
  );
}
