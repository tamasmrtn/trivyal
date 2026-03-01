import type { FindingStatus, Severity } from "@/lib/api/types";

const severityOptions: { value: Severity; label: string }[] = [
  { value: "CRITICAL", label: "Critical" },
  { value: "HIGH", label: "High" },
  { value: "MEDIUM", label: "Medium" },
  { value: "LOW", label: "Low" },
  { value: "UNKNOWN", label: "Unknown" },
];

const statusOptions: { value: FindingStatus; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "fixed", label: "Fixed" },
  { value: "accepted", label: "Accepted" },
  { value: "false_positive", label: "False Positive" },
];

interface FindingFiltersProps {
  severity: Severity | undefined;
  status: FindingStatus | undefined;
  onSeverityChange: (value: Severity | undefined) => void;
  onStatusChange: (value: FindingStatus | undefined) => void;
}

export function FindingFilters({
  severity,
  status,
  onSeverityChange,
  onStatusChange,
}: FindingFiltersProps) {
  return (
    <div className="flex gap-3">
      <select
        value={severity ?? ""}
        onChange={(e) =>
          onSeverityChange(
            (e.target.value || undefined) as Severity | undefined,
          )
        }
        aria-label="Filter by severity"
        className="border-input bg-background text-foreground rounded-md border px-3 py-2 text-sm"
      >
        <option value="">All Severities</option>
        {severityOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <select
        value={status ?? ""}
        onChange={(e) =>
          onStatusChange(
            (e.target.value || undefined) as FindingStatus | undefined,
          )
        }
        aria-label="Filter by status"
        className="border-input bg-background text-foreground rounded-md border px-3 py-2 text-sm"
      >
        <option value="">All Statuses</option>
        {statusOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
