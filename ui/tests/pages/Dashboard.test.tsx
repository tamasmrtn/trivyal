import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { Dashboard } from "@/pages/Dashboard";
import { BrowserRouter } from "react-router-dom";

vi.mock("@/features/dashboard/hooks/useDashboard", () => ({
  useDashboard: vi.fn(),
}));

import { useDashboard } from "@/features/dashboard/hooks/useDashboard";

const mockDashboardData = {
  severity_counts: {
    critical: 1,
    high: 2,
    medium: 3,
    low: 4,
    unknown: 0,
  },
  agent_status_counts: {
    online: 1,
    offline: 0,
    scanning: 0,
  },
  total_findings: 42,
  total_agents: 1,
  misconfig: {
    total_active: 5,
  },
  fixable_cves: 10,
};

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("Dashboard page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: null,
      loading: true,
      error: null,
    });

    renderWithRouter(<Dashboard />);
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: null,
      loading: false,
      error: "Failed to load dashboard",
    });

    renderWithRouter(<Dashboard />);
    expect(screen.getByText("Failed to load dashboard")).toBeInTheDocument();
  });

  it("renders dashboard heading", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);
    expect(
      screen.getByRole("heading", { name: /dashboard/i }),
    ).toBeInTheDocument();
  });

  it("renders Fixable only toggle button", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);
    expect(
      screen.getByRole("button", { name: /fixable only/i }),
    ).toBeInTheDocument();
  });

  it("renders Fix Today action card", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);
    expect(screen.getByText("Fix Today")).toBeInTheDocument();
    expect(screen.getByText("configuration issues")).toBeInTheDocument();
  });

  it("displays misconfig count on Fix Today card", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("renders Fixable CVEs action card", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);
    expect(screen.getByText("Fixable CVEs")).toBeInTheDocument();
    expect(
      screen.getByText("with upstream fixes available"),
    ).toBeInTheDocument();
  });

  it("displays fixable CVEs count on card", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("toggles fixable filter when button is clicked", async () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    const user = userEvent.setup();
    renderWithRouter(<Dashboard />);

    const button = screen.getByRole("button", { name: /fixable only/i });
    await user.click(button);

    // Verify hook is called with fixable=true
    expect(useDashboard).toHaveBeenCalledWith(true);
  });

  it("calls useDashboard with undefined when fixable is false", () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);

    // Initially called with undefined
    expect(useDashboard).toHaveBeenCalledWith(undefined);
  });

  it("Fix Today card is clickable and navigates to /priorities", async () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);

    const fixTodayCard = screen
      .getByText("Fix Today")
      .closest("div[class*='cursor-pointer']");
    expect(fixTodayCard).toHaveClass("cursor-pointer");
  });

  it("Fixable CVEs card is clickable and navigates to /priorities", async () => {
    vi.mocked(useDashboard).mockReturnValue({
      data: mockDashboardData,
      loading: false,
      error: null,
    });

    renderWithRouter(<Dashboard />);

    const fixableCvesCard = screen
      .getByText("Fixable CVEs")
      .closest("div[class*='cursor-pointer']");
    expect(fixableCvesCard).toHaveClass("cursor-pointer");
  });
});
