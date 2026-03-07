import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PackageCheck } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useImages } from "../hooks/useImages";
import type { Severity } from "@/lib/api/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

export function UpdateWhenYouCanSection() {
  const [fixableOnly, setFixableOnly] = useState(true);
  const navigate = useNavigate();

  const { data, total, loading, error } = useImages({
    fixable: fixableOnly,
    sort_by: "fixable_cves",
    sort_dir: "desc",
    page_size: 100,
  });

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Update When You Can</h2>
        <p className="text-muted-foreground text-sm">
          Images with CVEs that have a fix available upstream
        </p>
      </div>

      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setFixableOnly(!fixableOnly)}
          className={cn(fixableOnly && "bg-primary text-primary-foreground")}
        >
          Fixable only
        </Button>
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
          <PackageCheck className="text-muted-foreground h-5 w-5" />
          <p className="text-muted-foreground text-sm">
            No images with fixable CVEs. Either everything is up to date or no
            scans have run yet.
          </p>
        </div>
      )}

      {!loading && !error && data.length > 0 && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Image
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Tag
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Fixable CVEs
                </TableHead>
                <TableHead className="text-muted-foreground text-xs tracking-wide uppercase">
                  Total CVEs
                </TableHead>
                <TableHead className="text-muted-foreground hidden text-xs tracking-wide uppercase sm:table-cell">
                  Severity
                </TableHead>
                <TableHead className="text-muted-foreground hidden text-xs tracking-wide uppercase md:table-cell">
                  Agents
                </TableHead>
                <TableHead className="text-muted-foreground hidden text-xs tracking-wide uppercase sm:table-cell">
                  Last Scanned
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((image) => (
                <TableRow
                  key={image.image_name}
                  onClick={() =>
                    navigate(
                      `/findings?image_name=${encodeURIComponent(image.image_name)}&fixable=true`,
                    )
                  }
                  className="hover:bg-accent/50 cursor-pointer"
                >
                  <TableCell
                    className="max-w-[200px] truncate text-sm"
                    title={image.image_name}
                  >
                    {image.image_name}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {image.image_tag ?? "—"}
                  </TableCell>
                  <TableCell className="text-primary text-sm font-medium">
                    {image.fixable_cves}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {image.total_cves}
                  </TableCell>
                  <TableCell className="hidden sm:table-cell">
                    <div className="flex gap-1">
                      {(
                        ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as Severity[]
                      ).map(
                        (sev) =>
                          image.severity_breakdown[
                            sev.toLowerCase() as keyof typeof image.severity_breakdown
                          ] > 0 && (
                            <SeverityBadge
                              key={sev}
                              severity={sev}
                              className="px-1.5 py-0 text-[10px]"
                            />
                          ),
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground hidden text-xs md:table-cell">
                    {image.agents.map((a) => a.name).join(", ")}
                  </TableCell>
                  <TableCell className="text-muted-foreground hidden text-xs sm:table-cell">
                    {image.last_scanned ? formatDate(image.last_scanned) : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <p className="text-muted-foreground text-sm">
            {total} image{total !== 1 ? "s" : ""}
          </p>
        </>
      )}
    </section>
  );
}
