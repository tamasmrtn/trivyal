import { render, screen } from "@testing-library/react";
import { FindingTable } from "@/features/findings/components/FindingTable";
import type { FindingResponse } from "@/lib/api/types";

vi.mock("@/lib/api/findings", () => ({
  createAcceptance: vi.fn(),
}));

const mockFindings: FindingResponse[] = [
  {
    id: "f1",
    scan_result_id: "sr1",
    cve_id: "CVE-2026-1234",
    package_name: "openssl",
    installed_version: "1.1.1",
    fixed_version: "1.1.2",
    severity: "CRITICAL",
    status: "active",
    first_seen: "2026-02-01T00:00:00Z",
    last_seen: "2026-03-01T00:00:00Z",
  },
  {
    id: "f2",
    scan_result_id: "sr1",
    cve_id: "CVE-2026-5678",
    package_name: "curl",
    installed_version: "7.80.0",
    fixed_version: null,
    severity: "LOW",
    status: "fixed",
    first_seen: "2026-02-15T00:00:00Z",
    last_seen: "2026-02-20T00:00:00Z",
  },
];

describe("FindingTable", () => {
  it("renders empty state when no findings", () => {
    render(<FindingTable findings={[]} onAccepted={vi.fn()} />);
    expect(
      screen.getByText(/no findings match the current filters/i),
    ).toBeInTheDocument();
  });

  it("renders CVE IDs", () => {
    render(<FindingTable findings={mockFindings} onAccepted={vi.fn()} />);
    expect(screen.getByText("CVE-2026-1234")).toBeInTheDocument();
    expect(screen.getByText("CVE-2026-5678")).toBeInTheDocument();
  });

  it("renders package names", () => {
    render(<FindingTable findings={mockFindings} onAccepted={vi.fn()} />);
    expect(screen.getByText("openssl")).toBeInTheDocument();
    expect(screen.getByText("curl")).toBeInTheDocument();
  });

  it("renders severity badges", () => {
    render(<FindingTable findings={mockFindings} onAccepted={vi.fn()} />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("LOW")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<FindingTable findings={mockFindings} onAccepted={vi.fn()} />);
    expect(screen.getByText("Active")).toBeInTheDocument();
    // "Fixed" appears both as table header and status badge
    const fixedElements = screen.getAllByText("Fixed");
    expect(fixedElements.length).toBe(2);
  });

  it("renders dash when fixed_version is null", () => {
    render(<FindingTable findings={mockFindings} onAccepted={vi.fn()} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("shows accept risk button only for active findings", () => {
    render(<FindingTable findings={mockFindings} onAccepted={vi.fn()} />);
    expect(
      screen.getByLabelText("Accept risk for CVE-2026-1234"),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Accept risk for CVE-2026-5678"),
    ).not.toBeInTheDocument();
  });
});
