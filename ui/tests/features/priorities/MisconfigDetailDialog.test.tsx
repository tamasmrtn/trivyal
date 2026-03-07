import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { MisconfigDetailDialog } from "@/features/priorities/components/MisconfigDetailDialog";

vi.mock("@/lib/api/misconfigs", () => ({
  updateMisconfig: vi.fn(),
  createMisconfigAcceptance: vi.fn(),
}));

import {
  updateMisconfig,
  createMisconfigAcceptance,
} from "@/lib/api/misconfigs";

const mockFinding = {
  id: "misconf-123",
  check_id: "CKV_DOCKER_1",
  severity: "HIGH" as const,
  status: "active" as const,
  container_id: "abc123",
  container_name: "my-nginx",
  image_name: "nginx:latest",
  title: "Exposed port",
  fix_guideline: "Use USER directive",
  first_seen: "2026-03-01T10:00:00Z",
  last_seen: "2026-03-07T10:00:00Z",
};

describe("MisconfigDetailDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders dialog header with check id", () => {
    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={vi.fn()}
      />,
    );

    expect(screen.getByText("CKV_DOCKER_1")).toBeInTheDocument();
  });

  it("displays misconfig details", () => {
    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={vi.fn()}
      />,
    );

    expect(screen.getByText("Exposed port")).toBeInTheDocument();
    expect(screen.getByText("Use USER directive")).toBeInTheDocument();
    expect(screen.getByText("nginx:latest")).toBeInTheDocument();
  });

  it("displays status badge", () => {
    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={vi.fn()}
      />,
    );

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders Accept Risk button", () => {
    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: /accept risk/i }),
    ).toBeInTheDocument();
  });

  it("renders Mark False Positive button", () => {
    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: /mark false positive/i }),
    ).toBeInTheDocument();
  });

  it("calls createMisconfigAcceptance when Accept Risk is clicked", async () => {
    const onUpdated = vi.fn();
    vi.mocked(createMisconfigAcceptance).mockResolvedValue({
      id: "risk-123",
      misconfig_id: "misconf-123",
      note: "",
    });

    const user = userEvent.setup();

    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={onUpdated}
      />,
    );

    await user.click(screen.getByRole("button", { name: /accept risk/i }));

    expect(createMisconfigAcceptance).toHaveBeenCalledWith(
      "misconf-123",
      "Accepted via Priorities",
    );
    expect(onUpdated).toHaveBeenCalled();
  });

  it("calls updateMisconfig when Mark False Positive is clicked", async () => {
    const onUpdated = vi.fn();
    vi.mocked(updateMisconfig).mockResolvedValue({
      ...mockFinding,
      status: "false_positive",
    });

    const user = userEvent.setup();

    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={onUpdated}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: /mark false positive/i }),
    );

    expect(updateMisconfig).toHaveBeenCalledWith(
      "misconf-123",
      "false_positive",
    );
    expect(onUpdated).toHaveBeenCalled();
  });

  it("does not render when open is false", () => {
    const { container } = render(
      <MisconfigDetailDialog
        open={false}
        finding={mockFinding}
        onOpenChange={vi.fn()}
        onUpdated={vi.fn()}
      />,
    );

    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
  });

  it("calls onOpenChange when close button is clicked", async () => {
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    render(
      <MisconfigDetailDialog
        open={true}
        finding={mockFinding}
        onOpenChange={onOpenChange}
        onUpdated={vi.fn()}
      />,
    );

    const closeButton = screen.getByRole("button", { name: /close/i });
    await user.click(closeButton);

    expect(onOpenChange).toHaveBeenCalled();
  });
});
