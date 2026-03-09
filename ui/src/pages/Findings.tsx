import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useFixable } from "@/lib/hooks/useFixable";
import { FindingTable, FindingFilters, useFindings } from "@/features/findings";
import { useAgents } from "@/features/agents";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { FindingStatus, Severity } from "@/lib/api/types";

export function Findings() {
  const [searchParams] = useSearchParams();
  const [severity, setSeverity] = useState<Severity | undefined>();
  const [status, setStatus] = useState<FindingStatus | undefined>();
  const [agentId, setAgentId] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("first_seen");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const { data: agents } = useAgents({ page_size: 200 });

  const [fixable, toggleFixable] = useFixable();
  const imageName = searchParams.get("image_name") ?? undefined;

  const { data, total, loading, error, refetch } = useFindings({
    severity,
    status,
    agent_id: agentId,
    image_name: imageName,
    fixable: fixable || undefined,
    page,
    page_size: 50,
    sort_by: sortBy,
    sort_dir: sortDir,
  });

  const totalPages = Math.max(1, Math.ceil(total / 50));

  function handleAgentChange(value: string) {
    setAgentId(value || undefined);
    setPage(1);
  }

  function handleSeverityChange(value: Severity | undefined) {
    setSeverity(value);
    setPage(1);
  }

  function handleStatusChange(value: FindingStatus | undefined) {
    setStatus(value);
    setPage(1);
  }

  function handleSort(column: string) {
    if (sortBy === column) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(column);
      setSortDir("desc");
    }
    setPage(1);
  }

  function handleToggleFixable() {
    toggleFixable();
    setPage(1);
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading findings...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-destructive-foreground">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Findings</h1>
          {imageName && (
            <span className="bg-muted rounded-md px-2 py-1 text-sm">
              {imageName}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <select
            value={agentId ?? ""}
            onChange={(e) => handleAgentChange(e.target.value)}
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
          <FindingFilters
            severity={severity}
            status={status}
            onSeverityChange={handleSeverityChange}
            onStatusChange={handleStatusChange}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleFixable}
            className={cn(fixable && "bg-primary text-primary-foreground")}
          >
            Fixable only
          </Button>
        </div>
      </div>

      <FindingTable
        findings={data}
        onAccepted={refetch}
        sortBy={sortBy}
        sortDir={sortDir}
        onSort={handleSort}
      />

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-muted-foreground text-sm">
            {total} finding{total !== 1 ? "s" : ""} total
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="text-foreground hover:bg-accent hover:text-accent-foreground rounded-md border px-3 py-1 text-sm transition-colors disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-muted-foreground px-2 py-1 text-sm">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="text-foreground hover:bg-accent hover:text-accent-foreground rounded-md border px-3 py-1 text-sm transition-colors disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
