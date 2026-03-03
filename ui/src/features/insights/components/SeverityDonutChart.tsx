import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { InsightsSummary } from "@/lib/api/types";

interface Props {
  summary: InsightsSummary;
  severityCounts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

const SLICES = [
  { key: "critical" as const, label: "Critical", color: "#f87171" },
  { key: "high" as const, label: "High", color: "#fb923c" },
  { key: "medium" as const, label: "Medium", color: "#fbbf24" },
  { key: "low" as const, label: "Low", color: "#60a5fa" },
];

export function SeverityDonutChart({ summary, severityCounts }: Props) {
  const chartData = SLICES.map(({ key, label, color }) => ({
    name: label,
    value: severityCounts[key],
    color,
  })).filter((s) => s.value > 0);

  const total = summary.active_findings;

  if (total === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">
            Severity breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground flex h-32 items-center justify-center text-sm">
            No active findings.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">
          Severity breakdown
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={88}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} strokeWidth={0} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--color-card)",
                  border: "1px solid var(--color-border)",
                  borderRadius: 6,
                  fontSize: 12,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Centre label */}
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold">{total}</span>
            <span className="text-muted-foreground text-xs">active</span>
          </div>
        </div>
        <div className="mt-3 space-y-1">
          {SLICES.filter((s) => severityCounts[s.key] > 0).map(
            ({ key, label, color }) => (
              <div
                key={key}
                className="flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2 w-2 rounded-sm"
                    style={{ background: color }}
                  />
                  <span className="text-muted-foreground">{label}</span>
                </div>
                <span className="font-medium">{severityCounts[key]}</span>
              </div>
            ),
          )}
        </div>
      </CardContent>
    </Card>
  );
}
