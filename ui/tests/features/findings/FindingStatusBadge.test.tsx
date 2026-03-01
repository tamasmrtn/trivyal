import { render, screen } from "@testing-library/react";
import { FindingStatusBadge } from "@/features/findings/components/FindingStatusBadge";
import type { FindingStatus } from "@/lib/api/types";

describe("FindingStatusBadge", () => {
  it.each<[FindingStatus, string]>([
    ["active", "Active"],
    ["fixed", "Fixed"],
    ["accepted", "Accepted"],
    ["false_positive", "False Positive"],
  ])("renders label for status %s", (status, label) => {
    render(<FindingStatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("applies correct color for active status", () => {
    render(<FindingStatusBadge status="active" />);
    const badge = screen.getByText("Active");
    expect(badge.className).toContain("bg-red-600");
  });

  it("applies correct color for fixed status", () => {
    render(<FindingStatusBadge status="fixed" />);
    const badge = screen.getByText("Fixed");
    expect(badge.className).toContain("bg-green-600");
  });
});
