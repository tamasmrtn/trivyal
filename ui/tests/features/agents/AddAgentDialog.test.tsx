import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AddAgentDialog } from "@/features/agents/components/AddAgentDialog";
import { vi } from "vitest";

// Mock the API client
vi.mock("@/lib/api/agents", () => ({
  createAgent: vi.fn(),
}));

import { createAgent } from "@/lib/api/agents";

const mockCreateAgent = vi.mocked(createAgent);

describe("AddAgentDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Add Agent button", () => {
    render(<AddAgentDialog onCreated={vi.fn()} />);
    expect(screen.getByText("Add Agent")).toBeInTheDocument();
  });

  it("opens dialog on button click", async () => {
    const user = userEvent.setup();
    render(<AddAgentDialog onCreated={vi.fn()} />);

    await user.click(screen.getByText("Add Agent"));

    expect(screen.getByText("Agent name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. server-1")).toBeInTheDocument();
    expect(screen.getByText("Register")).toBeInTheDocument();
  });

  it("disables Register button when name is empty", async () => {
    const user = userEvent.setup();
    render(<AddAgentDialog onCreated={vi.fn()} />);

    await user.click(screen.getByText("Add Agent"));

    expect(screen.getByText("Register")).toBeDisabled();
  });

  it("shows deploy snippet after successful registration", async () => {
    mockCreateAgent.mockResolvedValue({
      id: "agent-1",
      name: "my-server",
      token: "test-token-123",
      hub_public_key: "test-pubkey-456",
    });

    const onCreated = vi.fn();
    const user = userEvent.setup();
    render(<AddAgentDialog onCreated={onCreated} />);

    await user.click(screen.getByText("Add Agent"));
    await user.type(screen.getByPlaceholderText("e.g. server-1"), "my-server");
    await user.click(screen.getByText("Register"));

    expect(await screen.findByText("Agent Registered")).toBeInTheDocument();
    expect(screen.getByText("test-token-123")).toBeInTheDocument();
    expect(screen.getByText("test-pubkey-456")).toBeInTheDocument();
    expect(screen.getByText(/trivyal\/agent:latest/)).toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    mockCreateAgent.mockRejectedValue(new Error("Agent name already exists"));

    const user = userEvent.setup();
    render(<AddAgentDialog onCreated={vi.fn()} />);

    await user.click(screen.getByText("Add Agent"));
    await user.type(screen.getByPlaceholderText("e.g. server-1"), "dup-name");
    await user.click(screen.getByText("Register"));

    expect(
      await screen.findByText("Agent name already exists"),
    ).toBeInTheDocument();
  });
});
