import { render, screen } from "@testing-library/react";
import {
  SeverityDonutChart,
  tooltipContentStyle,
} from "@/features/insights/components/SeverityDonutChart";
import type { InsightsSummary } from "@/lib/api/types";

const mockSummary: InsightsSummary = {
  active_findings: 10,
  critical_high: 5,
  new_in_period: 3,
  fix_rate: 30,
};

const mockCounts = { critical: 3, high: 2, medium: 4, low: 1 };
const zeroCounts = { critical: 0, high: 0, medium: 0, low: 0 };

describe("SeverityDonutChart", () => {
  it("shows empty state when no active findings", () => {
    render(
      <SeverityDonutChart
        summary={{ ...mockSummary, active_findings: 0 }}
        severityCounts={zeroCounts}
      />,
    );
    expect(screen.getByText(/no active findings/i)).toBeInTheDocument();
  });

  it("renders the chart title", () => {
    render(
      <SeverityDonutChart summary={mockSummary} severityCounts={mockCounts} />,
    );
    expect(screen.getByText("Severity breakdown")).toBeInTheDocument();
  });

  it("renders the total active count in the donut centre", () => {
    render(
      <SeverityDonutChart summary={mockSummary} severityCounts={mockCounts} />,
    );
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("renders severity legend rows for non-zero severities", () => {
    render(
      <SeverityDonutChart summary={mockSummary} severityCounts={mockCounts} />,
    );
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  describe("tooltipContentStyle", () => {
    it("sets foreground color for dark mode text readability", () => {
      expect(tooltipContentStyle.color).toBe("var(--color-foreground)");
    });

    it("sets card background", () => {
      expect(tooltipContentStyle.background).toBe("var(--color-card)");
    });

    it("sets border using design token", () => {
      expect(tooltipContentStyle.border).toBe("1px solid var(--color-border)");
    });
  });
});
