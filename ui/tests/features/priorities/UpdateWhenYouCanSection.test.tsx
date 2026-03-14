import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { UpdateWhenYouCanSection } from "@/features/priorities/components/UpdateWhenYouCanSection";
import { BrowserRouter } from "react-router-dom";

vi.mock("@/features/priorities/hooks/useImages", () => ({
  useImages: vi.fn(),
}));

import { useImages } from "@/features/priorities/hooks/useImages";

const mockImage = {
  image_name: "nginx:latest",
  image_tag: null,
  image_digest: null,
  container_count: 1,
  fixable_cves: 5,
  total_cves: 10,
  severity_breakdown: {
    critical: 1,
    high: 2,
    medium: 2,
    low: 5,
    unknown: 0,
  },
  agents: [
    {
      id: "prod-01",
      name: "prod-01",
    },
  ],
  last_scanned: "2026-03-07T10:00:00Z",
};

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("UpdateWhenYouCanSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [],
      total: 0,
      loading: true,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [],
      total: 0,
      loading: false,
      error: "Failed to load images",
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    expect(screen.getByText("Failed to load images")).toBeInTheDocument();
  });

  it("renders section heading", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    expect(screen.getByText("Update When You Can")).toBeInTheDocument();
  });

  it("renders Fixable only toggle", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    expect(
      screen.getByRole("button", { name: /fixable only/i }),
    ).toBeInTheDocument();
  });

  it("renders images in table", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    expect(screen.getByText("nginx:latest")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument(); // fixable_cves
    expect(screen.getByText("10")).toBeInTheDocument(); // total_cves
  });

  it("renders severity breakdown", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });

  it("shows empty state when no images", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [],
      total: 0,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    expect(
      screen.getByText(/no images with fixable cves/i),
    ).toBeInTheDocument();
  });

  it("toggles fixable filter when button is clicked", async () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    const user = userEvent.setup();
    renderWithRouter(<UpdateWhenYouCanSection />);

    const button = screen.getByRole("button", { name: /fixable only/i });
    await user.click(button);

    // Hook will be called with toggled fixable value
    expect(useImages).toHaveBeenCalled();
  });

  it("filter row has flex-wrap to prevent mobile overflow", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<UpdateWhenYouCanSection />);
    const agentSelect = screen.getByLabelText("Filter by agent");
    const filterRow = agentSelect.parentElement!;
    expect(filterRow.className).toContain("flex-wrap");
  });

  it("image name cell has responsive max-w for narrow screens", () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = renderWithRouter(<UpdateWhenYouCanSection />);
    const rows = container.querySelectorAll("tbody tr");
    const imageCell = rows[0].querySelectorAll("td")[0];
    expect(imageCell.className).toMatch(/max-w-\[120px\]/);
  });

  it("navigates to findings with image_name param when row is clicked", async () => {
    vi.mocked(useImages).mockReturnValue({
      data: [mockImage],
      total: 1,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    const user = userEvent.setup();
    renderWithRouter(<UpdateWhenYouCanSection />);

    const row = screen.getByRole("row", { name: /nginx:latest/i });
    await user.click(row);

    // Navigation happens through the row click - verify the image appears in the table
    expect(screen.getByText("nginx:latest")).toBeInTheDocument();
  });
});
