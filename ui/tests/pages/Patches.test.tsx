import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { Patches } from "@/pages/Patches";
import { BrowserRouter } from "react-router-dom";

vi.mock("@/store/auth", () => ({
  useAuthStore: vi.fn((selector: (s: { logout: () => void }) => unknown) =>
    selector({ logout: vi.fn() }),
  ),
}));

vi.mock("@/lib/api/patches", () => ({
  fetchPatches: vi.fn(),
}));

import { fetchPatches } from "@/lib/api/patches";

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("Patches page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders page heading", async () => {
    vi.mocked(fetchPatches).mockResolvedValue({
      data: [],
      total: 0,
      page: 1,
      page_size: 100,
    });

    renderWithRouter(<Patches />);
    expect(
      screen.getByRole("heading", { name: /patches/i }),
    ).toBeInTheDocument();
  });

  it("renders empty state", async () => {
    vi.mocked(fetchPatches).mockResolvedValue({
      data: [],
      total: 0,
      page: 1,
      page_size: 100,
    });

    renderWithRouter(<Patches />);

    expect(await screen.findByText(/no patches yet/i)).toBeInTheDocument();
  });

  it("renders table when patches exist", async () => {
    vi.mocked(fetchPatches).mockResolvedValue({
      data: [
        {
          id: "p1",
          agent_id: "a1",
          container_id: "c1",
          image_name: "nginx:1.25",
          patched_tag: "nginx:1.25-patched",
          status: "completed" as const,
          original_finding_count: 5,
          patched_finding_count: 0,
          error_message: null,
          requested_at: "2026-03-21T00:00:00Z",
          completed_at: "2026-03-21T00:01:00Z",
          restarts: [],
        },
      ],
      total: 1,
      page: 1,
      page_size: 100,
    });

    renderWithRouter(<Patches />);

    expect(await screen.findByText("nginx:1.25")).toBeInTheDocument();
  });
});
