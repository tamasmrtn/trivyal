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
];

describe("AgentTable", () => {
  it("renders empty state when no agents", () => {
    render(<AgentTable agents={[]} onDelete={vi.fn()} />);
    expect(screen.getByText(/no agents registered yet/i)).toBeInTheDocument();
  });

  it("renders agent names", () => {
    render(<AgentTable agents={mockAgents} onDelete={vi.fn()} />);
    expect(screen.getByText("server-1")).toBeInTheDocument();
    expect(screen.getByText("server-2")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<AgentTable agents={mockAgents} onDelete={vi.fn()} />);
    expect(screen.getByText("Online")).toBeInTheDocument();
    expect(screen.getByText("Offline")).toBeInTheDocument();
  });

  it("renders hostname from metadata", () => {
    render(<AgentTable agents={mockAgents} onDelete={vi.fn()} />);
    expect(screen.getByText("prod-host-1")).toBeInTheDocument();
  });

  it("renders dash when no host metadata", () => {
    render(<AgentTable agents={mockAgents} onDelete={vi.fn()} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("renders Never when last_seen is null", () => {
    render(<AgentTable agents={mockAgents} onDelete={vi.fn()} />);
    expect(screen.getByText("Never")).toBeInTheDocument();
  });

  it("calls onDelete when delete button is clicked", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    render(<AgentTable agents={mockAgents} onDelete={onDelete} />);

    const deleteBtn = screen.getByLabelText("Delete server-1");
    await user.click(deleteBtn);

    expect(onDelete).toHaveBeenCalledWith("abc123");
  });
});
