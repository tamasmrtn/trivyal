import { render, screen } from "@testing-library/react";
import { Settings } from "@/pages/Settings";
import { vi } from "vitest";

vi.mock("@/lib/api/settings", () => ({
  fetchSettings: vi.fn(),
  updateSettings: vi.fn(),
}));

import { fetchSettings } from "@/lib/api/settings";

const mockFetchSettings = vi.mocked(fetchSettings);

const mockSettings = {
  webhook_url: "https://hooks.slack.com/test",
  webhook_type: "slack" as const,
  notify_on_critical: true,
  notify_on_high: false,
};

describe("Settings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    mockFetchSettings.mockReturnValue(new Promise(() => {}));
    render(<Settings />);
    expect(screen.getByText(/loading settings/i)).toBeInTheDocument();
  });

  it("shows error state when fetch fails", async () => {
    mockFetchSettings.mockRejectedValue(new Error("Unauthorized"));
    render(<Settings />);
    expect(await screen.findByText("Unauthorized")).toBeInTheDocument();
  });

  it("renders Settings heading", async () => {
    mockFetchSettings.mockResolvedValue(mockSettings);
    render(<Settings />);
    expect(
      await screen.findByRole("heading", { name: /^settings$/i }),
    ).toBeInTheDocument();
  });

  it("renders Notifications card", async () => {
    mockFetchSettings.mockResolvedValue(mockSettings);
    render(<Settings />);
    expect(await screen.findByText("Notifications")).toBeInTheDocument();
  });

  it("renders the form with initial values from the API", async () => {
    mockFetchSettings.mockResolvedValue(mockSettings);
    render(<Settings />);

    expect(await screen.findByLabelText(/webhook url/i)).toHaveValue(
      "https://hooks.slack.com/test",
    );
    expect(screen.getByLabelText(/webhook type/i)).toHaveValue("slack");
    expect(screen.getByLabelText(/critical findings/i)).toBeChecked();
    expect(screen.getByLabelText(/high findings/i)).not.toBeChecked();
  });

  it("renders Save settings button", async () => {
    mockFetchSettings.mockResolvedValue(mockSettings);
    render(<Settings />);
    expect(
      await screen.findByRole("button", { name: /save settings/i }),
    ).toBeInTheDocument();
  });
});
