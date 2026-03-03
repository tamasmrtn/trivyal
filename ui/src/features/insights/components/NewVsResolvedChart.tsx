import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrendDayPoint } from "@/lib/api/types";

interface Props {
  days: TrendDayPoint[];
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// Only show days where something happened (new or resolved)
function filterActive(days: TrendDayPoint[]) {
  return days
    .filter((d) => d.new > 0 || d.resolved > 0)
    .map((d) => ({ ...d, resolved_neg: -d.resolved }));
}

export function NewVsResolvedChart({ days }: Props) {
  const chartData = filterActive(days);

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">
            New vs. resolved
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground flex h-32 items-center justify-center text-sm">
            No change events in this period.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">
          New vs. resolved
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-3 flex gap-4">
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-4 rounded-sm bg-red-500/70" />
            <span className="text-muted-foreground text-xs">New</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-4 rounded-sm bg-green-500/70" />
            <span className="text-muted-foreground text-xs">Resolved</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart
            data={chartData}
            margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <ReferenceLine y={0} stroke="var(--color-border)" />
            <Tooltip
              contentStyle={{
                background: "var(--color-card)",
                border: "1px solid var(--color-border)",
                borderRadius: 6,
                fontSize: 12,
              }}
              labelFormatter={(label: unknown) => formatDate(label as string)}
              formatter={(
                value: number | undefined,
                name: string | undefined,
              ) => [Math.abs(value ?? 0), name === "new" ? "New" : "Resolved"]}
            />
            <Bar dataKey="new" name="new" radius={[2, 2, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill="rgba(239,68,68,0.7)" />
              ))}
            </Bar>
            <Bar dataKey="resolved_neg" name="resolved" radius={[0, 0, 2, 2]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill="rgba(34,197,94,0.7)" />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
