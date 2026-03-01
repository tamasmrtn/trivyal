import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotificationSettingsForm } from "@/features/settings/components/NotificationSettingsForm";
import { vi } from "vitest";

vi.mock("@/lib/api/settings", () => ({
  updateSettings: vi.fn(),
}));

import { updateSettings } from "@/lib/api/settings";

const mockUpdateSettings = vi.mocked(updateSettings);

const defaultInitial = {
  webhook_url: null,
  webhook_type: null,
  notify_on_critical: true,
  notify_on_high: false,
} as const;

describe("NotificationSettingsForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Save settings button", () => {
    render(
      <NotificationSettingsForm initial={defaultInitial} onSaved={vi.fn()} />,
    );
    expect(
      screen.getByRole("button", { name: /save settings/i }),
    ).toBeInTheDocument();
  });

  it("pre-fills webhook URL from initial value", () => {
    render(
      <NotificationSettingsForm
        initial={{
          ...defaultInitial,
          webhook_url: "https://hooks.example.com",
        }}
        onSaved={vi.fn()}
      />,
    );
    expect(screen.getByLabelText(/webhook url/i)).toHaveValue(
      "https://hooks.example.com",
    );
  });

  it("pre-selects webhook type from initial value", () => {
    render(
      <NotificationSettingsForm
        initial={{ ...defaultInitial, webhook_type: "slack" }}
        onSaved={vi.fn()}
      />,
    );
    expect(screen.getByLabelText(/webhook type/i)).toHaveValue("slack");
  });

  it("pre-checks notify_on_critical checkbox when true", () => {
    render(
      <NotificationSettingsForm
        initial={{ ...defaultInitial, notify_on_critical: true }}
        onSaved={vi.fn()}
      />,
    );
    expect(screen.getByLabelText(/critical findings/i)).toBeChecked();
  });

  it("leaves notify_on_high unchecked when false", () => {
    render(
      <NotificationSettingsForm
        initial={{ ...defaultInitial, notify_on_high: false }}
        onSaved={vi.fn()}
      />,
    );
    expect(screen.getByLabelText(/high findings/i)).not.toBeChecked();
  });

  it("calls updateSettings with correct payload on submit", async () => {
    mockUpdateSettings.mockResolvedValue({
      webhook_url: "https://hooks.slack.com/test",
      webhook_type: "slack",
      notify_on_critical: true,
      notify_on_high: true,
    });

    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(
      <NotificationSettingsForm initial={defaultInitial} onSaved={onSaved} />,
    );

    await user.clear(screen.getByLabelText(/webhook url/i));
    await user.type(
      screen.getByLabelText(/webhook url/i),
      "https://hooks.slack.com/test",
    );
    await user.selectOptions(screen.getByLabelText(/webhook type/i), "slack");
    await user.click(screen.getByLabelText(/high findings/i));
    await user.click(screen.getByRole("button", { name: /save settings/i }));

    expect(mockUpdateSettings).toHaveBeenCalledWith({
      webhook_url: "https://hooks.slack.com/test",
      webhook_type: "slack",
      notify_on_critical: true,
      notify_on_high: true,
    });
    expect(onSaved).toHaveBeenCalled();
  });

  it("sends null webhook_url when field is empty", async () => {
    mockUpdateSettings.mockResolvedValue({
      ...defaultInitial,
      webhook_url: null,
      notify_on_critical: true,
      notify_on_high: false,
    });

    const user = userEvent.setup();
    render(
      <NotificationSettingsForm initial={defaultInitial} onSaved={vi.fn()} />,
    );

    await user.click(screen.getByRole("button", { name: /save settings/i }));

    expect(mockUpdateSettings).toHaveBeenCalledWith(
      expect.objectContaining({ webhook_url: null }),
    );
  });

  it("sends null webhook_type when None is selected", async () => {
    mockUpdateSettings.mockResolvedValue({
      ...defaultInitial,
      webhook_type: null,
    });

    const user = userEvent.setup();
    render(
      <NotificationSettingsForm
        initial={{ ...defaultInitial, webhook_type: "discord" }}
        onSaved={vi.fn()}
      />,
    );

    await user.selectOptions(
      screen.getByLabelText(/webhook type/i),
      "None / Generic",
    );
    await user.click(screen.getByRole("button", { name: /save settings/i }));

    expect(mockUpdateSettings).toHaveBeenCalledWith(
      expect.objectContaining({ webhook_type: null }),
    );
  });

  it("shows Saved feedback after successful save", async () => {
    mockUpdateSettings.mockResolvedValue({ ...defaultInitial });

    const user = userEvent.setup();
    render(
      <NotificationSettingsForm initial={defaultInitial} onSaved={vi.fn()} />,
    );

    await user.click(screen.getByRole("button", { name: /save settings/i }));

    expect(
      await screen.findByRole("button", { name: /^saved$/i }),
    ).toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    mockUpdateSettings.mockRejectedValue(new Error("Server error"));

    const user = userEvent.setup();
    render(
      <NotificationSettingsForm initial={defaultInitial} onSaved={vi.fn()} />,
    );

    await user.click(screen.getByRole("button", { name: /save settings/i }));

    expect(await screen.findByText("Server error")).toBeInTheDocument();
  });

  it("disables form controls while saving", async () => {
    let resolve!: () => void;
    mockUpdateSettings.mockReturnValue(
      new Promise<typeof defaultInitial>((r) => {
        resolve = () => r({ ...defaultInitial });
      }),
    );

    const user = userEvent.setup();
    render(
      <NotificationSettingsForm initial={defaultInitial} onSaved={vi.fn()} />,
    );

    await user.click(screen.getByRole("button", { name: /save settings/i }));

    expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
    expect(screen.getByLabelText(/webhook url/i)).toBeDisabled();

    resolve();
  });
});
