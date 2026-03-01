import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardSummary } from "@/lib/api/types";
import {
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  Info,
  HelpCircle,
  Server,
  Wifi,
  WifiOff,
  Loader,
} from "lucide-react";

interface SummaryCardsProps {
  data: DashboardSummary;
}

const severityCards = [
  {
    key: "critical" as const,
    label: "Critical",
    icon: ShieldAlert,
    color: "text-red-600",
  },
  {
    key: "high" as const,
    label: "High",
    icon: AlertTriangle,
    color: "text-orange-600",
  },
  {
    key: "medium" as const,
    label: "Medium",
    icon: AlertCircle,
    color: "text-amber-600",
  },
  { key: "low" as const, label: "Low", icon: Info, color: "text-blue-600" },
  {
    key: "unknown" as const,
    label: "Unknown",
    icon: HelpCircle,
    color: "text-gray-600",
  },
] as const;

const agentStatusCards = [
  {
    key: "online" as const,
    label: "Online",
    icon: Wifi,
    color: "text-green-600",
  },
  {
    key: "offline" as const,
    label: "Offline",
    icon: WifiOff,
    color: "text-red-600",
  },
  {
    key: "scanning" as const,
    label: "Scanning",
    icon: Loader,
    color: "text-primary",
  },
] as const;

export function SummaryCards({ data }: SummaryCardsProps) {
  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-4 text-lg font-semibold">Vulnerabilities</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {severityCards.map(({ key, label, icon: Icon, color }) => (
            <Card key={key}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{label}</CardTitle>
                <Icon className={`h-4 w-4 ${color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.severity_counts[key]}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold">Agents</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {agentStatusCards.map(({ key, label, icon: Icon, color }) => (
            <Card key={key}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{label}</CardTitle>
                <Icon className={`h-4 w-4 ${color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {data.agent_status_counts[key]}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Active Findings
              </CardTitle>
              <ShieldAlert className="text-muted-foreground h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.total_findings}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Agents
              </CardTitle>
              <Server className="text-muted-foreground h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.total_agents}</div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
