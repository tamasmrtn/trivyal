import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import type { TopCve } from "@/lib/api/types";

interface Props {
  cves: TopCve[];
}

export function TopCvesTable({ cves }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Top CVEs</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {cves.length === 0 ? (
          <div className="text-muted-foreground flex h-32 items-center justify-center text-sm">
            No active findings in this period.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  CVE
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Severity
                </TableHead>
                <TableHead className="text-muted-foreground text-right text-xs tracking-wide uppercase">
                  Containers
                </TableHead>
                <TableHead className="text-muted-foreground text-right text-xs tracking-wide uppercase">
                  Agents
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cves.map((cve) => (
                <TableRow key={cve.cve_id}>
                  <TableCell className="font-mono text-xs">
                    {cve.cve_id}
                  </TableCell>
                  <TableCell>
                    <SeverityBadge severity={cve.severity} />
                  </TableCell>
                  <TableCell className="text-right text-sm">
                    {cve.containers}
                  </TableCell>
                  <TableCell className="text-right text-sm">
                    {cve.agents}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
