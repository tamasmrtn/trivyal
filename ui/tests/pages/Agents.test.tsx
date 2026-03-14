import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Agents } from "@/pages/Agents";
import { vi } from "vitest";

vi.mock("@/lib/api/agents", () => ({
  fetchAgents: vi.fn(),
  deleteAgent: vi.fn(),
  createAgent: vi.fn(),
}));

vi.mock("@/lib/api/scans", () => ({
  triggerScan: vi.fn(),
}));

import { fetchAgents } from "@/lib/api/agents";
import { triggerScan } from "@/lib/api/scans";

const mockFetchAgents = vi.mocked(fetchAgents);
const mockTriggerScan = vi.mocked(triggerScan);

const mockPagedAgents = {
  data: [
    {
      id: "abc123",
      name: "server-1",
      status: "online" as const,
      last_seen: "2026-03-01T10:00:00Z",
      host_metadata: { hostname: "prod-host-1" },
      created_at: "2026-02-01T00:00:00Z",
    },
    {
      id: "def456",
      name: "server-2",
      status: "offline" as const,
      last_seen: null,
      host_metadata: null,
      created_at: "2026-02-15T00:00:00Z",
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
};

describe("Agents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    mockFetchAgents.mockReturnValue(new Promise(() => {}));
    render(<Agents />);
    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows error state when fetch fails", async () => {
    mockFetchAgents.mockRejectedValue(new Error("Unauthorized"));
    render(<Agents />);
    expect(await screen.findByText("Unauthorized")).toBeInTheDocument();
  });

  it("renders the Agents heading", async () => {
    mockFetchAgents.mockResolvedValue(mockPagedAgents);
    render(<Agents />);
    expect(
      await screen.findByRole("heading", { name: /^agents$/i }),
    ).toBeInTheDocument();
  });

  it("renders agent names after load", async () => {
    mockFetchAgents.mockResolvedValue(mockPagedAgents);
    render(<Agents />);
    expect(await screen.findByText("server-1")).toBeInTheDocument();
    expect(screen.getByText("server-2")).toBeInTheDocument();
  });

  it("calls triggerScan with the agent id when scan button is clicked", async () => {
    mockFetchAgents.mockResolvedValue(mockPagedAgents);
    mockTriggerScan.mockResolvedValue({ job_id: "job-abc" });
    const user = userEvent.setup();

    render(<Agents />);
    await screen.findByText("server-1");

    await user.click(screen.getByLabelText("Scan server-1"));

    expect(mockTriggerScan).toHaveBeenCalledWith("abc123");
  });

  it("scan button for offline agent is disabled", async () => {
    mockFetchAgents.mockResolvedValue(mockPagedAgents);
    render(<Agents />);
    await screen.findByText("server-2");

    expect(screen.getByLabelText("Scan server-2")).toBeDisabled();
  });

  it("does not throw when triggerScan rejects (best-effort)", async () => {
    mockFetchAgents.mockResolvedValue(mockPagedAgents);
    mockTriggerScan.mockRejectedValue(new Error("Agent is not connected"));
    const user = userEvent.setup();

    render(<Agents />);
    await screen.findByText("server-1");

    await expect(
      user.click(screen.getByLabelText("Scan server-1")),
    ).resolves.not.toThrow();
  });
});
