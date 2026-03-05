import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("@/store/auth", () => ({
  useAuthStore: vi.fn((selector: (s: { logout: () => void }) => unknown) =>
    selector({ logout: vi.fn() }),
  ),
}));

import { PageLayout } from "@/components/common/PageLayout";

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
});
