import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AgentTable } from "@/features/agents/components/AgentTable";
import type { AgentResponse } from "@/lib/api/types";

const mockAgents: AgentResponse[] = [
  {
    id: "abc123",
    name: "server-1",
    status: "online",
    last_seen: "2026-03-01T10:00:00Z",
    host_metadata: { hostname: "prod-host-1" },
    created_at: "2026-02-01T00:00:00Z",
  },
  {
    id: "def456",
    name: "server-2",
    status: "offline",
    last_seen: null,
    host_metadata: null,
    created_at: "2026-02-15T00:00:00Z",
  },
  {
    id: "ghi789",
    name: "server-3",
    status: "scanning",
    last_seen: "2026-03-01T09:00:00Z",
    host_metadata: { hostname: "scan-host-3" },
    created_at: "2026-02-20T00:00:00Z",
  },
];

describe("AgentTable", () => {
  it("renders empty state when no agents", () => {
    render(
      <AgentTable agents={[]} onDelete={vi.fn()} onTriggerScan={vi.fn()} />,
    );
    expect(screen.getByText(/no agents registered/i)).toBeInTheDocument();
  });

  it("renders agent names", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByText("server-1")).toBeInTheDocument();
    expect(screen.getByText("server-2")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByText("Online")).toBeInTheDocument();
    expect(screen.getByText("Offline")).toBeInTheDocument();
  });

  it("renders hostname from metadata", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByText("prod-host-1")).toBeInTheDocument();
  });

  it("renders dash when no host metadata", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("renders Never when last_seen is null", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByText("Never")).toBeInTheDocument();
  });

  it("calls onDelete when delete button is clicked and confirmed", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(
      <AgentTable
        agents={mockAgents}
        onDelete={onDelete}
        onTriggerScan={vi.fn()}
      />,
    );

    const deleteBtn = screen.getByLabelText("Delete server-1");
    await user.click(deleteBtn);

    expect(onDelete).toHaveBeenCalledWith("abc123");
    vi.restoreAllMocks();
  });

  it("renders a scan button for each agent row", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Scan server-1")).toBeInTheDocument();
    expect(screen.getByLabelText("Scan server-2")).toBeInTheDocument();
    expect(screen.getByLabelText("Scan server-3")).toBeInTheDocument();
  });

  it("scan button is enabled for online agents", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Scan server-1")).not.toBeDisabled();
  });

  it("scan button is disabled for offline agents", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Scan server-2")).toBeDisabled();
  });

  it("scan button is disabled for scanning agents", () => {
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Scan server-3")).toBeDisabled();
  });

  it("calls onTriggerScan with the agent id when clicked", async () => {
    const onTriggerScan = vi.fn(() => new Promise<void>(() => {}));
    const user = userEvent.setup();
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={onTriggerScan}
      />,
    );

    await user.click(screen.getByLabelText("Scan server-1"));

    expect(onTriggerScan).toHaveBeenCalledWith("abc123");
  });

  it("disables the scan button while the request is in-flight", async () => {
    const onTriggerScan = vi.fn(() => new Promise<void>(() => {}));
    const user = userEvent.setup();
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={onTriggerScan}
      />,
    );

    await user.click(screen.getByLabelText("Scan server-1"));

    expect(screen.getByLabelText("Scan server-1")).toBeDisabled();
  });

  it("does not call onDelete without confirmation", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    // Simulate user cancelling the confirm dialog
    vi.spyOn(window, "confirm").mockReturnValue(false);

    render(
      <AgentTable
        agents={mockAgents}
        onDelete={onDelete}
        onTriggerScan={vi.fn()}
      />,
    );

    await user.click(screen.getByLabelText("Delete server-1"));

    expect(onDelete).not.toHaveBeenCalled();
    vi.restoreAllMocks();
  });

  it("calls onDelete after user confirms", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(
      <AgentTable
        agents={mockAgents}
        onDelete={onDelete}
        onTriggerScan={vi.fn()}
      />,
    );

    await user.click(screen.getByLabelText("Delete server-1"));

    expect(onDelete).toHaveBeenCalledWith("abc123");
    vi.restoreAllMocks();
  });

  it("scan and delete buttons have gap-2 between them to avoid accidental taps", () => {
    const { container } = render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={vi.fn()}
      />,
    );
    // The action cell div wrapping both buttons should use gap-2
    const actionDivs = container.querySelectorAll("td > div");
    const hasScanAndDelete = Array.from(actionDivs).some(
      (div) => div.className.includes("gap-2") && div.children.length === 2,
    );
    expect(hasScanAndDelete).toBe(true);
  });

  it("re-enables the scan button after the request resolves", async () => {
    let resolve!: () => void;
    const onTriggerScan = vi.fn(
      () =>
        new Promise<void>((res) => {
          resolve = res;
        }),
    );
    const user = userEvent.setup();
    render(
      <AgentTable
        agents={mockAgents}
        onDelete={vi.fn()}
        onTriggerScan={onTriggerScan}
      />,
    );

    await user.click(screen.getByLabelText("Scan server-1"));
    expect(screen.getByLabelText("Scan server-1")).toBeDisabled();

    resolve();

    expect(
      await screen.findByRole("button", { name: "Scan server-1" }),
    ).not.toBeDisabled();
  });
});
