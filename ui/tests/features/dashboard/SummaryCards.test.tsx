import { render, screen } from "@testing-library/react";
import { SummaryCards } from "@/features/dashboard/components/SummaryCards";
import type { DashboardSummary } from "@/lib/api/types";

const mockData: DashboardSummary = {
  severity_counts: {
    critical: 5,
    high: 12,
    medium: 23,
    low: 8,
    unknown: 2,
  },
  agent_status_counts: {
    online: 3,
    offline: 1,
    scanning: 4,
  },
  total_findings: 50,
  total_agents: 7,
};

describe("SummaryCards", () => {
  beforeEach(() => {
    render(<SummaryCards data={mockData} />);
  });

  it("renders all severity counts", () => {
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("23")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders severity labels", () => {
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });

  it("renders agent status counts", () => {
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("renders agent status labels", () => {
    expect(screen.getByText("Online")).toBeInTheDocument();
    expect(screen.getByText("Offline")).toBeInTheDocument();
    expect(screen.getByText("Scanning")).toBeInTheDocument();
  });

  it("renders total findings and agents", () => {
    expect(screen.getByText("50")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("Total Active Findings")).toBeInTheDocument();
    expect(screen.getByText("Total Agents")).toBeInTheDocument();
  });
});
