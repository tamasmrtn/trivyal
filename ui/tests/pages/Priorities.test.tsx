import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { Priorities } from "@/pages/Priorities";
import { BrowserRouter } from "react-router-dom";

vi.mock("@/store/auth", () => ({
  useAuthStore: vi.fn((selector: (s: { logout: () => void }) => unknown) =>
    selector({ logout: vi.fn() }),
  ),
}));

vi.mock("@/lib/api/misconfigs", () => ({
  fetchMisconfigs: vi.fn(),
}));

vi.mock("@/lib/api/images", () => ({
  fetchImages: vi.fn(),
}));

vi.mock("@/features/priorities/components/FixTodaySection", () => ({
  FixTodaySection: () => <div data-testid="fix-today">Fix Today Section</div>,
}));

vi.mock("@/features/priorities/components/UpdateWhenYouCanSection", () => ({
  UpdateWhenYouCanSection: () => (
    <div data-testid="update-when-you-can">Update When You Can Section</div>
  ),
}));

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("Priorities page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders page heading", () => {
    renderWithRouter(<Priorities />);
    expect(
      screen.getByRole("heading", { name: /priorities/i }),
    ).toBeInTheDocument();
  });

  it("renders page description", () => {
    renderWithRouter(<Priorities />);
    expect(
      screen.getByText(/what to act on across your infrastructure/i),
    ).toBeInTheDocument();
  });

  it("renders FixTodaySection", () => {
    renderWithRouter(<Priorities />);
    expect(screen.getByTestId("fix-today")).toBeInTheDocument();
  });

  it("renders UpdateWhenYouCanSection", () => {
    renderWithRouter(<Priorities />);
    expect(screen.getByTestId("update-when-you-can")).toBeInTheDocument();
  });

  it("renders divider between sections", () => {
    const { container } = renderWithRouter(<Priorities />);
    const divider = container.querySelector(".border-t");
    expect(divider).toBeInTheDocument();
  });
});
