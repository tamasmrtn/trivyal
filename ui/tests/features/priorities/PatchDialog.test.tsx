import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { PatchDialog } from "@/features/priorities/components/PatchDialog";
import { BrowserRouter } from "react-router-dom";

vi.mock("@/store/auth", () => ({
  useAuthStore: Object.assign(
    vi.fn((selector: (s: { token: string }) => unknown) =>
      selector({ token: "test-token" }),
    ),
    {
      getState: () => ({ token: "test-token" }),
    },
  ),
}));

vi.mock("@/lib/api/patches", () => ({
  createPatch: vi.fn(),
  subscribePatchLogs: vi.fn(),
  fetchPatch: vi.fn(),
  triggerRestart: vi.fn(),
}));

import { createPatch, subscribePatchLogs } from "@/lib/api/patches";

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("PatchDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders dialog title when open", () => {
    vi.mocked(createPatch).mockResolvedValue({
      id: "p1",
      agent_id: "a1",
      container_id: "c1",
      image_name: "nginx",
      patched_tag: null,
      status: "running",
      original_finding_count: null,
      patched_finding_count: null,
      error_message: null,
      requested_at: "2026-03-21T00:00:00Z",
      completed_at: null,
      restarts: [],
    });
    vi.mocked(subscribePatchLogs).mockReturnValue(() => {});

    renderWithRouter(
      <PatchDialog
        open={true}
        onOpenChange={() => {}}
        agentId="a1"
        containerId="c1"
        imageName="nginx"
      />,
    );

    expect(screen.getByText("Patch nginx")).toBeInTheDocument();
  });

  it("shows waiting message before logs arrive", () => {
    vi.mocked(createPatch).mockReturnValue(new Promise(() => {})); // Never resolves
    renderWithRouter(
      <PatchDialog
        open={true}
        onOpenChange={() => {}}
        agentId="a1"
        containerId="c1"
        imageName="redis"
      />,
    );

    expect(screen.getByText(/waiting for copa output/i)).toBeInTheDocument();
  });
});
