import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Findings } from "@/pages/Findings";
import { vi } from "vitest";

vi.mock("@/lib/api/findings", () => ({
  fetchFindings: vi.fn(),
  createAcceptance: vi.fn(),
}));

import { fetchFindings } from "@/lib/api/findings";

const mockFetchFindings = vi.mocked(fetchFindings);

const mockPagedFindings = {
  data: [
    {
      id: "f1",
      scan_result_id: "sr1",
      cve_id: "CVE-2026-1234",
      package_name: "openssl",
      installed_version: "1.1.1",
      fixed_version: "1.1.2",
      severity: "CRITICAL" as const,
      description: null,
      status: "active" as const,
      container_name: "nginx:latest",
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
      severity: "HIGH" as const,
      description: null,
      status: "fixed" as const,
      container_name: null,
      first_seen: "2026-02-15T00:00:00Z",
      last_seen: "2026-02-20T00:00:00Z",
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
};

function renderFindings() {
  return render(
    <MemoryRouter>
      <Findings />
    </MemoryRouter>,
  );
}

describe("Findings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    mockFetchFindings.mockReturnValue(new Promise(() => {}));
    renderFindings();
    expect(document.querySelectorAll(".animate-pulse").length).toBeGreaterThan(
      0,
    );
  });

  it("shows error state when fetch fails", async () => {
    mockFetchFindings.mockRejectedValue(new Error("Unauthorized"));
    renderFindings();
    expect(await screen.findByText("Unauthorized")).toBeInTheDocument();
  });

  it("renders the Findings heading", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    renderFindings();
    expect(
      await screen.findByRole("heading", { name: /^findings$/i }),
    ).toBeInTheDocument();
  });

  it("renders severity and status filter selects", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    renderFindings();
    await screen.findByRole("heading", { name: /^findings$/i });
    expect(screen.getByLabelText("Filter by severity")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by status")).toBeInTheDocument();
  });

  it("renders findings after load", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    renderFindings();
    expect(await screen.findByText("CVE-2026-1234")).toBeInTheDocument();
    expect(screen.getByText("CVE-2026-5678")).toBeInTheDocument();
  });

  it("renders severity badges", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    renderFindings();
    await screen.findByText("CVE-2026-1234");
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("does not show pagination when total fits on one page", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings); // total: 2, page_size: 50
    renderFindings();
    await screen.findByText("CVE-2026-1234");
    expect(
      screen.queryByRole("button", { name: /previous/i }),
    ).not.toBeInTheDocument();
  });

  it("shows pagination when total exceeds page size", async () => {
    mockFetchFindings.mockResolvedValue({ ...mockPagedFindings, total: 60 });
    renderFindings();
    await screen.findByText("CVE-2026-1234");
    expect(
      screen.getByRole("button", { name: /previous/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /next/i })).toBeInTheDocument();
  });

  it("renders Fixable only toggle button", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    renderFindings();
    await screen.findByRole("heading", { name: /^findings$/i });
    expect(
      screen.getByRole("button", { name: /fixable only/i }),
    ).toBeInTheDocument();
  });

  it("displays image name badge when image_name param is set", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    render(
      <MemoryRouter initialEntries={["/?image_name=nginx:latest"]}>
        <Findings />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^findings$/i });
    expect(screen.getAllByText("nginx:latest").length).toBeGreaterThan(0);
  });

  it("passes image_name param to API when set", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    render(
      <MemoryRouter initialEntries={["/?image_name=nginx:latest"]}>
        <Findings />
      </MemoryRouter>,
    );
    await screen.findByText("CVE-2026-1234");
    expect(mockFetchFindings).toHaveBeenCalledWith(
      expect.objectContaining({ image_name: "nginx:latest" }),
    );
  });

  it("filter controls container has flex-wrap to prevent mobile overflow", async () => {
    mockFetchFindings.mockResolvedValue(mockPagedFindings);
    renderFindings();
    await screen.findByRole("heading", { name: /^findings$/i });

    const agentSelect = screen.getByLabelText("Filter by agent");
    // The direct parent of the agent select is the controls container
    const controlsDiv = agentSelect.parentElement!;
    expect(controlsDiv.className).toContain("flex-wrap");
  });

  it("pagination buttons have py-2 for adequate touch target height", async () => {
    mockFetchFindings.mockResolvedValue({ ...mockPagedFindings, total: 60 });
    renderFindings();
    await screen.findByText("CVE-2026-1234");

    const prevBtn = screen.getByRole("button", { name: /previous/i });
    expect(prevBtn.className).toContain("py-2");
  });
});
