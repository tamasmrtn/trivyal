import { render, screen } from "@testing-library/react";
import { InsightsSummaryCards } from "@/features/insights/components/InsightsSummaryCards";
import type { InsightsSummary } from "@/lib/api/types";

const mockSummary: InsightsSummary = {
  active_findings: 42,
  critical_high: 15,
  new_in_period: 8,
  fix_rate: 62.5,
};

describe("InsightsSummaryCards", () => {
  beforeEach(() => {
    render(<InsightsSummaryCards summary={mockSummary} />);
  });

  it("renders active findings count", () => {
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Active findings")).toBeInTheDocument();
  });

  it("renders critical+high count", () => {
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("Critical + High")).toBeInTheDocument();
  });

  it("renders new in period count", () => {
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("New this period")).toBeInTheDocument();
  });

  it("renders fix rate with percent sign", () => {
    expect(screen.getByText("62.5%")).toBeInTheDocument();
    expect(screen.getByText("Fix rate")).toBeInTheDocument();
  });
});
