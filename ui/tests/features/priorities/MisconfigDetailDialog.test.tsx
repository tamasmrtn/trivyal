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

const mockMisconfig = {
  id: "misconf-123",
  check_id: "CKV_DOCKER_1",
  severity: "HIGH" as const,
  status: "active" as const,
  container_id: "abc123",
  image_name: "nginx:latest",
  issue: "Exposed port",
  fix: "Use USER directive",
  first_seen: "2026-03-01T10:00:00Z",
};

describe("MisconfigDetailDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders dialog header with check id", () => {
    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByText("CKV_DOCKER_1")).toBeInTheDocument();
  });

  it("displays misconfig details", () => {
    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByText("Exposed port")).toBeInTheDocument();
    expect(screen.getByText("Use USER directive")).toBeInTheDocument();
    expect(screen.getByText("nginx:latest")).toBeInTheDocument();
  });

  it("displays status badge", () => {
    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders Accept Risk button", () => {
    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: /accept risk/i }),
    ).toBeInTheDocument();
  });

  it("renders Mark False Positive button", () => {
    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: /mark false positive/i }),
    ).toBeInTheDocument();
  });

  it("calls createMisconfigAcceptance when Accept Risk is clicked", async () => {
    const onAction = vi.fn();
    vi.mocked(createMisconfigAcceptance).mockResolvedValue({
      id: "risk-123",
      misconfig_id: "misconf-123",
      note: "",
    });

    const user = userEvent.setup();

    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={onAction}
      />,
    );

    await user.click(screen.getByRole("button", { name: /accept risk/i }));

    expect(createMisconfigAcceptance).toHaveBeenCalledWith("misconf-123", {});
    expect(onAction).toHaveBeenCalled();
  });

  it("calls updateMisconfig when Mark False Positive is clicked", async () => {
    const onAction = vi.fn();
    vi.mocked(updateMisconfig).mockResolvedValue({
      ...mockMisconfig,
      status: "false_positive",
    });

    const user = userEvent.setup();

    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={onAction}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: /mark false positive/i }),
    );

    expect(updateMisconfig).toHaveBeenCalledWith("misconf-123", {
      status: "false_positive",
    });
    expect(onAction).toHaveBeenCalled();
  });

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <MisconfigDetailDialog
        isOpen={false}
        misconfig={mockMisconfig}
        onClose={vi.fn()}
        onAction={vi.fn()}
      />,
    );

    // Dialog should not be visible
    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
  });

  it("calls onClose when X button is clicked", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <MisconfigDetailDialog
        isOpen={true}
        misconfig={mockMisconfig}
        onClose={onClose}
        onAction={vi.fn()}
      />,
    );

    const closeButton = screen.getByRole("button", { name: /close/i });
    await user.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });
});
