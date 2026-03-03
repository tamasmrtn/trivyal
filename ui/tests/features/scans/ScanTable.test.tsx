import { render, screen } from "@testing-library/react";
import { ScanTable } from "@/features/scans/components/ScanTable";
import type { ScanResultResponse } from "@/lib/api/types";

const mockScans: ScanResultResponse[] = [
  {
    id: "aabbccdd1122334455667788",
    container_id: "c1d2e3f4aabbccdd",
    agent_id: "a1b2c3d4eeff0011",
    agent_name: null,
    container_name: null,
    scanned_at: "2026-03-01T02:00:00Z",
    critical_count: 3,
    high_count: 7,
    medium_count: 12,
    low_count: 5,
    unknown_count: 0,
  },
  {
    id: "eeff00112233445566778899",
    container_id: "f1e2d3c4bbaa9988",
    agent_id: "b2c3d4e5ffaa1122",
    agent_name: null,
    container_name: null,
    scanned_at: "2026-02-28T02:00:00Z",
    critical_count: 0,
    high_count: 0,
    medium_count: 0,
    low_count: 0,
    unknown_count: 0,
  },
];

describe("ScanTable", () => {
  it("renders empty state when no scans", () => {
    render(<ScanTable scans={[]} />);
    expect(screen.getByText(/no scans found/i)).toBeInTheDocument();
  });

  it("renders a row per scan", () => {
    render(<ScanTable scans={mockScans} />);
    const rows = screen.getAllByRole("row");
    // header row + 2 data rows
    expect(rows).toHaveLength(3);
  });

  it("shows short agent and container IDs", () => {
    render(<ScanTable scans={mockScans} />);
    expect(screen.getByText("a1b2c3d4")).toBeInTheDocument();
    expect(screen.getByText("c1d2e3f4")).toBeInTheDocument();
  });

  it("shows non-zero counts", () => {
    render(<ScanTable scans={mockScans} />);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows dashes for zero counts", () => {
    render(<ScanTable scans={mockScans} />);
    // Second scan has all zeros — expect multiple dashes
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(5);
  });
});
