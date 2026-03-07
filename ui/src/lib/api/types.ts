export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
}

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";

export type FindingStatus = "active" | "fixed" | "accepted" | "false_positive";

export type AgentStatus = "online" | "offline" | "scanning";

export interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
  unknown: number;
}

export interface AgentStatusCounts {
  online: number;
  offline: number;
  scanning: number;
}

export interface MisconfigCounts {
  high: number;
  medium: number;
  total_active: number;
}

export interface DashboardSummary {
  severity_counts: SeverityCounts;
  agent_status_counts: AgentStatusCounts;
  total_findings: number;
  total_agents: number;
  fixable_cves: number;
  misconfig: MisconfigCounts;
}

export interface AgentResponse {
  id: string;
  name: string;
  status: AgentStatus;
  last_seen: string | null;
  host_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface AgentRegistered {
  id: string;
  name: string;
  token: string;
  hub_public_key: string;
}

export interface FindingResponse {
  id: string;
  scan_result_id: string;
  cve_id: string;
  package_name: string;
  installed_version: string;
  fixed_version: string | null;
  severity: Severity;
  description: string | null;
  status: FindingStatus;
  container_name: string | null;
  first_seen: string;
  last_seen: string;
}

export interface ScanResultResponse {
  id: string;
  container_id: string;
  agent_id: string;
  agent_name: string | null;
  container_name: string | null;
  scanned_at: string;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  unknown_count: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type WebhookType = "slack" | "discord" | "ntfy" | null;

export interface SettingsResponse {
  webhook_url: string | null;
  webhook_type: WebhookType;
  notify_on_critical: boolean;
  notify_on_high: boolean;
}

export interface InsightsSummary {
  active_findings: number;
  critical_high: number;
  new_in_period: number;
  fix_rate: number;
}

export interface TrendDayPoint {
  date: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  new: number;
  resolved: number;
}

export interface TrendResponse {
  days: TrendDayPoint[];
  scan_events: string[];
}

export interface AgentDayPoint {
  date: string;
  total: number;
}

export interface AgentTrend {
  agent_id: string;
  name: string;
  days: AgentDayPoint[];
}

export interface AgentTrendResponse {
  agents: AgentTrend[];
  scan_events: string[];
}

export interface TopCve {
  cve_id: string;
  severity: Severity;
  containers: number;
  agents: number;
}

export type MisconfigStatus =
  | "active"
  | "fixed"
  | "accepted"
  | "false_positive";

export interface MisconfigFindingResponse {
  id: string;
  container_id: string;
  container_name: string | null;
  image_name: string | null;
  check_id: string;
  severity: Severity;
  title: string;
  fix_guideline: string;
  status: MisconfigStatus;
  first_seen: string;
  last_seen: string;
}

export interface AgentRef {
  id: string;
  name: string;
}

export interface ImageResponse {
  image_name: string;
  image_tag: string | null;
  image_digest: string | null;
  container_count: number;
  agents: AgentRef[];
  total_cves: number;
  fixable_cves: number;
  severity_breakdown: SeverityCounts;
  last_scanned: string | null;
}
