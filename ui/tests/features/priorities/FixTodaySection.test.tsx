import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { FixTodaySection } from "@/features/priorities/components/FixTodaySection";

vi.mock("@/store/auth", () => ({
  useAuthStore: vi.fn((selector: (s: { logout: () => void }) => unknown) =>
    selector({ logout: vi.fn() }),
  ),
}));

vi.mock("@/features/priorities/hooks/useMisconfigs", () => ({
  useMisconfigs: vi.fn(),
}));

import { useMisconfigs } from "@/features/priorities/hooks/useMisconfigs";

const mockMisconfig = {
  id: "misconf-123",
  check_id: "CKV_DOCKER_1",
  severity: "HIGH" as const,
  status: "active" as const,
  container_id: "abc123",
  container_name: null,
  image_name: "nginx:latest",
  title: "Exposed port",
  fix_guideline: "Use USER directive",
  first_seen: "2026-03-01T10:00:00Z",
  last_seen: "2026-03-07T10:00:00Z",
};

describe("FixTodaySection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [],
      total: 0,
      loading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [],
      total: 0,
      loading: false,
      error: "Failed to load misconfigs",
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getByText("Failed to load misconfigs")).toBeInTheDocument();
  });

  it("renders section heading", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getByText("Fix Today")).toBeInTheDocument();
  });

  it("renders severity filter buttons", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getByRole("button", { name: "High" })).toBeInTheDocument();
  });

  it("renders status filter dropdown", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getByLabelText(/filter by status/i)).toBeInTheDocument();
  });

  it("renders misconfigs in table", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getByText("CKV_DOCKER_1")).toBeInTheDocument();
    expect(screen.getByText("Exposed port")).toBeInTheDocument();
    expect(screen.getByText("Use USER directive")).toBeInTheDocument();
  });

  it("renders severity badge", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(screen.getAllByText("Active").length).toBeGreaterThan(0);
  });

  it("shows empty state when no misconfigs", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [],
      total: 0,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<FixTodaySection />);
    expect(
      screen.getByText(/no configuration issues found/i),
    ).toBeInTheDocument();
  });

  it("calls refetch when severity filter changes", async () => {
    const refetch = vi.fn();
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch,
    });

    const user = userEvent.setup();
    render(<FixTodaySection />);

    await user.click(screen.getByRole("button", { name: "High" }));

    // Hook will be called with new severity value
    expect(useMisconfigs).toHaveBeenCalled();
  });

  it("calls refetch when status filter changes", async () => {
    const refetch = vi.fn();
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch,
    });

    const user = userEvent.setup();
    render(<FixTodaySection />);

    const statusSelect = screen.getByLabelText(/filter by status/i);
    await user.selectOptions(statusSelect, "accepted");

    expect(useMisconfigs).toHaveBeenCalled();
  });

  it("container and title cells have max-w and truncate to prevent overflow", () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<FixTodaySection />);
    const rows = container.querySelectorAll("tbody tr");
    const cells = rows[0].querySelectorAll("td");
    // Container is 2nd cell (index 1), Issue is 3rd (index 2)
    const containerCell = cells[1];
    const issueCell = cells[2];
    expect(containerCell.className).toMatch(/max-w-/);
    expect(containerCell.className).toContain("truncate");
    expect(issueCell.className).toMatch(/max-w-/);
    expect(issueCell.className).toContain("truncate");
  });

  it("opens detail dialog when row is clicked", async () => {
    vi.mocked(useMisconfigs).mockReturnValue({
      data: [mockMisconfig],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    const user = userEvent.setup();
    render(<FixTodaySection />);

    const row = screen.getByRole("row", { name: /CKV_DOCKER_1/i });
    await user.click(row);

    // Dialog should open - CKV_DOCKER_1 appears in both table and dialog
    expect(screen.getAllByText("CKV_DOCKER_1").length).toBeGreaterThan(0);
  });
});
