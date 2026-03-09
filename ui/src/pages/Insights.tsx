import { useState } from "react";
import { useFixable } from "@/lib/hooks/useFixable";
import {
  useInsights,
  InsightsSummaryCards,
  VulnerabilityTrendChart,
  AgentTrendChart,
  SeverityDonutChart,
  TopCvesTable,
} from "@/features/insights";
import { useAgents } from "@/features/agents";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const WINDOWS = [
  { label: "7d", value: 7 },
  { label: "30d", value: 30 },
  { label: "90d", value: 90 },
];

export function Insights() {
  const [window, setWindow] = useState(30);
  const [agentId, setAgentId] = useState<string | undefined>();
  const [fixable, toggleFixable] = useFixable();
  const { data: agents } = useAgents({ page_size: 200 });
  const { data, loading, error } = useInsights(
    window,
    fixable || undefined,
    agentId,
  );

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading insights...</p>
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

  if (!data) return null;

  // Derive current severity breakdown from the last day of trend data
  const lastDay = data.trend.days[data.trend.days.length - 1];
  const severityCounts = lastDay
    ? {
        critical: lastDay.critical,
        high: lastDay.high,
        medium: lastDay.medium,
        low: lastDay.low,
      }
    : { critical: 0, high: 0, medium: 0, low: 0 };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold">Insights</h1>
        <div className="flex items-center gap-3">
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
          <div className="flex items-center gap-1 rounded-md border p-1">
            {WINDOWS.map(({ label, value }) => (
              <button
                key={value}
                onClick={() => setWindow(value)}
                className={cn(
                  "rounded px-3 py-1 text-sm font-medium transition-colors",
                  window === value
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={toggleFixable}
            className={cn(fixable && "bg-primary text-primary-foreground")}
          >
            Fixable only
          </Button>
        </div>
      </div>

      {/* Summary cards */}
      <InsightsSummaryCards summary={data.summary} />

      {/* Vulnerability trend */}
      <VulnerabilityTrendChart data={data.trend} />

      {/* Per-agent trend */}
      <AgentTrendChart data={data.agentsTrend} />

      {/* Bottom row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <TopCvesTable cves={data.topCves} />
        <SeverityDonutChart
          summary={data.summary}
          severityCounts={severityCounts}
        />
      </div>
    </div>
  );
}
