import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("@/store/auth", () => ({
  useAuthStore: vi.fn((selector: (s: { logout: () => void }) => unknown) =>
    selector({ logout: vi.fn() }),
  ),
}));

vi.mock("@/lib/api/dashboard", () => ({
  fetchDashboardSummary: vi.fn(),
}));

import { PageLayout } from "@/components/common/PageLayout";
import { fetchDashboardSummary } from "@/lib/api/dashboard";

function renderLayout(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<PageLayout />}>
          <Route index element={<div>Home content</div>} />
          <Route path="/agents" element={<div>Agents content</div>} />
          <Route path="/findings" element={<div>Findings content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("PageLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock the dashboard summary for all tests
    vi.mocked(fetchDashboardSummary).mockResolvedValue({
      misconfig: { total_active: 0 },
      fixable_cves: 0,
    });
  });

  it("renders the outlet content", () => {
    renderLayout();
    expect(screen.getByText("Home content")).toBeInTheDocument();
  });

  it("renders nav links in the sidebar", () => {
    renderLayout();
    const links = screen.getAllByRole("link", { name: /dashboard/i });
    expect(links.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the hamburger button for mobile nav", () => {
    renderLayout();
    expect(
      screen.getByRole("button", { name: /open menu/i }),
    ).toBeInTheDocument();
  });

  it("opens the nav drawer when hamburger is clicked", async () => {
    const user = userEvent.setup();
    renderLayout();

    await user.click(screen.getByRole("button", { name: /open menu/i }));

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(
      within(dialog).getByRole("link", { name: /dashboard/i }),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole("link", { name: /agents/i }),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole("link", { name: /findings/i }),
    ).toBeInTheDocument();
  });

  it("closes the nav drawer when a nav link is clicked", async () => {
    const user = userEvent.setup();
    renderLayout();

    await user.click(screen.getByRole("button", { name: /open menu/i }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    const dialog = screen.getByRole("dialog");
    await user.click(within(dialog).getByRole("link", { name: /agents/i }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("navigates to the correct page when nav link in drawer is clicked", async () => {
    const user = userEvent.setup();
    renderLayout();

    await user.click(screen.getByRole("button", { name: /open menu/i }));

    const dialog = screen.getByRole("dialog");
    await user.click(within(dialog).getByRole("link", { name: /agents/i }));

    expect(screen.getByText("Agents content")).toBeInTheDocument();
  });

  it("renders log out button in the drawer", async () => {
    const user = userEvent.setup();
    renderLayout();

    await user.click(screen.getByRole("button", { name: /open menu/i }));

    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog).getByRole("button", { name: /log out/i }),
    ).toBeInTheDocument();
  });

  it("fetches priority count on mount", () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue({
      misconfig: { total_active: 5 },
      fixable_cves: 10,
    });

    renderLayout();

    expect(fetchDashboardSummary).toHaveBeenCalled();
  });

  it("renders Priorities nav link", () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue({
      misconfig: { total_active: 0 },
      fixable_cves: 0,
    });

    renderLayout();

    const prioritiesLink = screen.getByRole("link", { name: /priorities/i });
    expect(prioritiesLink).toBeInTheDocument();
  });

  it("does not render priority count badge when count is zero", () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue({
      misconfig: { total_active: 0 },
      fixable_cves: 0,
    });

    renderLayout();

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("renders priority count badge when misconfig count is greater than zero", async () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue({
      misconfig: { total_active: 5 },
      fixable_cves: 0,
    });

    renderLayout();

    // Wait for the badge to render (count should be 5)
    const badge = await screen.findByText("5");
    expect(badge).toBeInTheDocument();
  });

  it("renders priority count badge when fixable CVEs count is greater than zero", async () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue({
      misconfig: { total_active: 0 },
      fixable_cves: 10,
    });

    renderLayout();

    // Wait for the badge to render (count should be 10)
    const badge = await screen.findByText("10");
    expect(badge).toBeInTheDocument();
  });

  it("renders sum of misconfig and fixable CVEs in badge", async () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue({
      misconfig: { total_active: 5 },
      fixable_cves: 10,
    });

    renderLayout();

    // Wait for the badge to render (count should be 15)
    const badge = await screen.findByText("15");
    expect(badge).toBeInTheDocument();
  });

  it("hamburger button has h-10 for an adequate touch target", () => {
    renderLayout();
    const btn = screen.getByRole("button", { name: /open menu/i });
    expect(btn.className).toMatch(/h-10/);
  });

  it("nav links in mobile drawer have py-3 for adequate touch target height", async () => {
    const user = userEvent.setup();
    renderLayout();
    await user.click(screen.getByRole("button", { name: /open menu/i }));

    const dialog = screen.getByRole("dialog");
    const dashboardLink = within(dialog).getByRole("link", {
      name: /dashboard/i,
    });
    expect(dashboardLink.className).toMatch(/py-3/);
  });
});
