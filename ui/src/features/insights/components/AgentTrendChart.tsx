import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AgentTrendResponse } from "@/lib/api/types";

interface Props {
  data: AgentTrendResponse;
}

// Distinguishable palette separate from severity colours
const AGENT_COLORS = [
  "#00d4b4", // teal (primary)
  "#a78bfa", // violet
  "#38bdf8", // sky
  "#f472b6", // pink
  "#34d399", // emerald
  "#fb923c", // orange (only here, not severity)
  "#e879f9", // fuchsia
  "#94a3b8", // slate
];

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// Merge per-agent daily arrays into a flat array keyed by date
function buildChartData(data: AgentTrendResponse) {
  if (data.agents.length === 0) return [];
  const dateMap = new Map<string, Record<string, number>>();
  for (const agent of data.agents) {
    for (const point of agent.days) {
      if (!dateMap.has(point.date)) dateMap.set(point.date, {});
      dateMap.get(point.date)![agent.agent_id] = point.total;
    }
  }
  return Array.from(dateMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, counts]) => ({ date, ...counts }));
}

export function AgentTrendChart({ data }: Props) {
  if (data.agents.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">
            Per-agent trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground flex h-32 items-center justify-center text-sm">
            No agents registered.
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = buildChartData(data);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">
          Per-agent trend
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-3 flex flex-wrap gap-4">
          {data.agents.map((agent, i) => (
            <div key={agent.agent_id} className="flex items-center gap-1.5">
              <span
                className="inline-block h-2 w-4 rounded-sm"
                style={{
                  background: AGENT_COLORS[i % AGENT_COLORS.length],
                }}
              />
              <span className="text-muted-foreground font-mono text-xs">
                {agent.name}
              </span>
            </div>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart
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
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                background: "var(--color-card)",
                border: "1px solid var(--color-border)",
                borderRadius: 6,
                fontSize: 12,
              }}
              labelFormatter={(label: unknown) => formatDate(label as string)}
            />
            {data.agents.map((agent, i) => (
              <Line
                key={agent.agent_id}
                type="monotone"
                dataKey={agent.agent_id}
                name={agent.name}
                stroke={AGENT_COLORS[i % AGENT_COLORS.length]}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
