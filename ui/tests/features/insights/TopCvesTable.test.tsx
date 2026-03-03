import { render, screen } from "@testing-library/react";
import { TopCvesTable } from "@/features/insights/components/TopCvesTable";
import type { TopCve } from "@/lib/api/types";

const mockCves: TopCve[] = [
  {
    cve_id: "CVE-2024-1234",
    severity: "CRITICAL",
    containers: 5,
    agents: 2,
  },
  {
    cve_id: "CVE-2023-9999",
    severity: "HIGH",
    containers: 2,
    agents: 1,
  },
];

describe("TopCvesTable", () => {
  it("renders empty state when no CVEs", () => {
    render(<TopCvesTable cves={[]} />);
    expect(
      screen.getByText(/no active findings in this period/i),
    ).toBeInTheDocument();
  });

  it("renders a row per CVE", () => {
    render(<TopCvesTable cves={mockCves} />);
    const rows = screen.getAllByRole("row");
    // header + 2 data rows
    expect(rows).toHaveLength(3);
  });

  it("renders CVE IDs", () => {
    render(<TopCvesTable cves={mockCves} />);
    expect(screen.getByText("CVE-2024-1234")).toBeInTheDocument();
    expect(screen.getByText("CVE-2023-9999")).toBeInTheDocument();
  });

  it("renders container and agent counts", () => {
    render(<TopCvesTable cves={mockCves} />);
    expect(screen.getByText("5")).toBeInTheDocument();
    // "2" appears as both container count for second CVE and agent count for first CVE
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1);
  });

  it("renders severity badges", () => {
    render(<TopCvesTable cves={mockCves} />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });
});
