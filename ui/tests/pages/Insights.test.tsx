import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Insights } from "@/pages/Insights";
import { vi } from "vitest";

vi.mock("@/lib/api/insights", () => ({
  fetchInsightsSummary: vi.fn(),
  fetchInsightsTrend: vi.fn(),
  fetchAgentsTrend: vi.fn(),
  fetchTopCves: vi.fn(),
}));

import {
  fetchInsightsSummary,
  fetchInsightsTrend,
  fetchAgentsTrend,
  fetchTopCves,
} from "@/lib/api/insights";

const mockSummary = {
  active_findings: 10,
  critical_high: 3,
  new_in_period: 4,
  fix_rate: 25.0,
};

const mockTrend = {
  days: [
    {
      date: "2026-02-01",
      critical: 2,
      high: 1,
      medium: 3,
      low: 4,
      new: 2,
      resolved: 0,
    },
    {
      date: "2026-03-03",
      critical: 2,
      high: 1,
      medium: 3,
      low: 4,
      new: 2,
      resolved: 0,
    },
  ],
  scan_events: ["2026-03-03T10:00:00"],
};

const mockAgentsTrend = {
  agents: [
    {
      agent_id: "abc",
      name: "prod-01",
      days: [{ date: "2026-03-03", total: 6 }],
    },
  ],
  scan_events: ["2026-03-03T10:00:00"],
};

const mockTopCves = [
  {
    cve_id: "CVE-2024-1234",
    severity: "CRITICAL" as const,
    containers: 3,
    agents: 1,
  },
];

function setupMocks() {
  vi.mocked(fetchInsightsSummary).mockResolvedValue(mockSummary);
  vi.mocked(fetchInsightsTrend).mockResolvedValue(mockTrend);
  vi.mocked(fetchAgentsTrend).mockResolvedValue(mockAgentsTrend);
  vi.mocked(fetchTopCves).mockResolvedValue(mockTopCves);
}

describe("Insights page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    vi.mocked(fetchInsightsSummary).mockReturnValue(new Promise(() => {}));
    vi.mocked(fetchInsightsTrend).mockReturnValue(new Promise(() => {}));
    vi.mocked(fetchAgentsTrend).mockReturnValue(new Promise(() => {}));
    vi.mocked(fetchTopCves).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    expect(screen.getByText(/loading insights/i)).toBeInTheDocument();
  });

  it("shows error state when fetch fails", async () => {
    vi.mocked(fetchInsightsSummary).mockRejectedValue(
      new Error("Unauthorized"),
    );
    vi.mocked(fetchInsightsTrend).mockResolvedValue(mockTrend);
    vi.mocked(fetchAgentsTrend).mockResolvedValue(mockAgentsTrend);
    vi.mocked(fetchTopCves).mockResolvedValue(mockTopCves);

    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Unauthorized")).toBeInTheDocument();
  });

  it("renders the Insights heading", async () => {
    setupMocks();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    expect(
      await screen.findByRole("heading", { name: /^insights$/i }),
    ).toBeInTheDocument();
  });

  it("renders time range selector buttons", async () => {
    setupMocks();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^insights$/i });
    expect(screen.getByRole("button", { name: "7d" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "30d" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "90d" })).toBeInTheDocument();
  });

  it("renders summary card labels and values", async () => {
    setupMocks();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    // Wait for data to load
    expect(await screen.findByText("Active findings")).toBeInTheDocument();
    expect(screen.getByText("Critical + High")).toBeInTheDocument();
    expect(screen.getByText("New this period")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
  });

  it("re-fetches when time window changes", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^insights$/i });

    await user.click(screen.getByRole("button", { name: "7d" }));

    expect(fetchInsightsSummary).toHaveBeenCalledWith(7, undefined, undefined);
  });

  it("renders Fixable only toggle button", async () => {
    setupMocks();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^insights$/i });
    expect(
      screen.getByRole("button", { name: /fixable only/i }),
    ).toBeInTheDocument();
  });

  it("passes fixable param to API when true", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^insights$/i });

    // Click fixable button
    const fixableBtn = screen.getByRole("button", { name: /fixable only/i });
    await user.click(fixableBtn);

    // Verify API is called with fixable=true
    expect(fetchInsightsSummary).toHaveBeenCalledWith(30, true, undefined);
  });

  it("inner controls container has flex-wrap to prevent mobile overflow", async () => {
    setupMocks();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^insights$/i });

    const agentSelect = screen.getByLabelText("Filter by agent");
    const controlsDiv = agentSelect.parentElement!;
    expect(controlsDiv.className).toContain("flex-wrap");
  });

  it("time window buttons have py-2 for adequate touch target height", async () => {
    setupMocks();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^insights$/i });

    const btn7d = screen.getByRole("button", { name: "7d" });
    expect(btn7d.className).toContain("py-2");
  });

  it("fetches with correct params when fixable and window are set", async () => {
    setupMocks();
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <Insights />
      </MemoryRouter>,
    );
    await screen.findByRole("heading", { name: /^insights$/i });

    // Change window to 7d
    await user.click(screen.getByRole("button", { name: "7d" }));

    // Click fixable button
    const fixableBtn = screen.getByRole("button", { name: /fixable only/i });
    await user.click(fixableBtn);

    // Both params should be passed
    expect(fetchInsightsSummary).toHaveBeenCalledWith(7, true, undefined);
  });
});
