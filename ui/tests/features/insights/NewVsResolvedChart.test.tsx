import { render, screen } from "@testing-library/react";
import {
  NewVsResolvedChart,
  tooltipContentStyle,
} from "@/features/insights/components/NewVsResolvedChart";
import type { TrendDayPoint } from "@/lib/api/types";

const activeDays: TrendDayPoint[] = [
  {
    date: "2026-03-01",
    critical: 2,
    high: 1,
    medium: 3,
    low: 4,
    new: 5,
    resolved: 2,
  },
];

const emptyDays: TrendDayPoint[] = [
  {
    date: "2026-03-01",
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    new: 0,
    resolved: 0,
  },
];

describe("NewVsResolvedChart", () => {
  it("shows empty state when no active days", () => {
    render(<NewVsResolvedChart days={emptyDays} />);
    expect(
      screen.getByText(/no change events in this period/i),
    ).toBeInTheDocument();
  });

  it("renders the chart title", () => {
    render(<NewVsResolvedChart days={activeDays} />);
    expect(screen.getByText("New vs. resolved")).toBeInTheDocument();
  });

  it("renders legend labels", () => {
    render(<NewVsResolvedChart days={activeDays} />);
    expect(screen.getByText("New")).toBeInTheDocument();
    expect(screen.getByText("Resolved")).toBeInTheDocument();
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
