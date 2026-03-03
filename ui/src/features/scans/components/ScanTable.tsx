import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ScanResultResponse } from "@/lib/api/types";

interface ScanTableProps {
  scans: ScanResultResponse[];
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

function shortId(id: string): string {
  return id.slice(0, 8);
}

function Count({ value, className }: { value: number; className: string }) {
  if (value === 0) {
    return <span className="text-muted-foreground">—</span>;
  }
  return <span className={`font-semibold ${className}`}>{value}</span>;
}

export function ScanTable({ scans }: ScanTableProps) {
  if (scans.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-lg border">
        <p className="text-muted-foreground text-sm">No scans found.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Scanned At</TableHead>
            <TableHead>Agent</TableHead>
            <TableHead>Container</TableHead>
            <TableHead className="text-center">Critical</TableHead>
            <TableHead className="text-center">High</TableHead>
            <TableHead className="text-center">Medium</TableHead>
            <TableHead className="text-center">Low</TableHead>
            <TableHead className="text-center">Unknown</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scans.map((scan) => (
            <TableRow key={scan.id}>
              <TableCell className="whitespace-nowrap">
                {formatDate(scan.scanned_at)}
              </TableCell>
              <TableCell>
                {scan.agent_name ?? (
                  <span className="font-mono text-xs">
                    {shortId(scan.agent_id)}
                  </span>
                )}
              </TableCell>
              <TableCell>
                {scan.container_name ?? (
                  <span className="font-mono text-xs">
                    {shortId(scan.container_id)}
                  </span>
                )}
              </TableCell>
              <TableCell className="text-center">
                <Count value={scan.critical_count} className="text-red-600" />
              </TableCell>
              <TableCell className="text-center">
                <Count value={scan.high_count} className="text-orange-600" />
              </TableCell>
              <TableCell className="text-center">
                <Count value={scan.medium_count} className="text-amber-600" />
              </TableCell>
              <TableCell className="text-center">
                <Count value={scan.low_count} className="text-blue-600" />
              </TableCell>
              <TableCell className="text-center">
                <Count
                  value={scan.unknown_count}
                  className="text-muted-foreground"
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
