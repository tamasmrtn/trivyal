import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
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

function renderTable(findings = mockFindings) {
  return render(
    <MemoryRouter>
      <FindingTable findings={findings} onAccepted={vi.fn()} />
    </MemoryRouter>,
  );
}

describe("FindingTable", () => {
  it("renders empty state when no findings", () => {
    renderTable([]);
    expect(
      screen.getByText(/no findings match the current filters/i),
    ).toBeInTheDocument();
  });

  it("renders CVE IDs as links to detail page", () => {
    renderTable();
    const link1 = screen.getByRole("link", { name: "CVE-2026-1234" });
    expect(link1).toBeInTheDocument();
    expect(link1).toHaveAttribute("href", "/findings/f1");

    const link2 = screen.getByRole("link", { name: "CVE-2026-5678" });
    expect(link2).toHaveAttribute("href", "/findings/f2");
  });

  it("renders package names", () => {
    renderTable();
    expect(screen.getByText("openssl")).toBeInTheDocument();
    expect(screen.getByText("curl")).toBeInTheDocument();
  });

  it("renders severity badges", () => {
    renderTable();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("LOW")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    renderTable();
    expect(screen.getByText("Active")).toBeInTheDocument();
    // "Fixed" appears both as table header and status badge
    const fixedElements = screen.getAllByText("Fixed");
    expect(fixedElements.length).toBe(2);
  });

  it("renders dash when fixed_version is null", () => {
    renderTable();
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("shows accept risk button only for active findings", () => {
    renderTable();
    expect(
      screen.getByLabelText("Accept risk for CVE-2026-1234"),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Accept risk for CVE-2026-5678"),
    ).not.toBeInTheDocument();
  });
});
