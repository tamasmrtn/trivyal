import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useFixable } from "@/lib/hooks/useFixable";
import { PackageCheck } from "lucide-react";
import { useAgents } from "@/features/agents";
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

export function UpdateWhenYouCanSection() {
  const [fixableOnly, toggleFixableOnly] = useFixable();
  const [agentId, setAgentId] = useState<string | undefined>();
  const navigate = useNavigate();

  const { data: agents } = useAgents({ page_size: 200 });
  const { data, total, loading, error } = useImages({
    agent_id: agentId,
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

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={agentId ?? ""}
          onChange={(e) => setAgentId(e.target.value || undefined)}
          aria-label="Filter by agent"
          className="bg-input text-foreground focus:ring-ring rounded-md border px-3 py-2 text-sm focus:ring-2 focus:outline-none"
        >
          <option value="">All Agents</option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
        <Button
          variant="outline"
          size="sm"
          onClick={toggleFixableOnly}
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
                    className="max-w-[120px] truncate text-sm sm:max-w-[200px]"
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
