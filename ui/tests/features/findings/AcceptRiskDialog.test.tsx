import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AcceptRiskDialog } from "@/features/findings/components/AcceptRiskDialog";
import { createAcceptance } from "@/lib/api/findings";

vi.mock("@/lib/api/findings", () => ({
  createAcceptance: vi.fn(),
}));

describe("AcceptRiskDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders trigger button with correct aria-label", () => {
    render(
      <AcceptRiskDialog
        findingId="f1"
        cveId="CVE-2026-1234"
        onAccepted={vi.fn()}
      />,
    );
    expect(
      screen.getByLabelText("Accept risk for CVE-2026-1234"),
    ).toBeInTheDocument();
  });

  it("opens dialog when trigger is clicked", async () => {
    const user = userEvent.setup();
    render(
      <AcceptRiskDialog
        findingId="f1"
        cveId="CVE-2026-1234"
        onAccepted={vi.fn()}
      />,
    );

    await user.click(screen.getByLabelText("Accept risk for CVE-2026-1234"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText("Reason")).toBeInTheDocument();
  });

  it("disables submit when reason is empty", async () => {
    const user = userEvent.setup();
    render(
      <AcceptRiskDialog
        findingId="f1"
        cveId="CVE-2026-1234"
        onAccepted={vi.fn()}
      />,
    );

    await user.click(screen.getByLabelText("Accept risk for CVE-2026-1234"));
    const submitBtn = screen.getByRole("button", { name: "Accept Risk" });
    expect(submitBtn).toBeDisabled();
  });

  it("calls createAcceptance and onAccepted on submit", async () => {
    const onAccepted = vi.fn();
    const user = userEvent.setup();
    vi.mocked(createAcceptance).mockResolvedValue({
      id: "a1",
      finding_id: "f1",
      reason: "Not exploitable",
      accepted_by: "admin",
      expires_at: null,
      created_at: "2026-03-01T00:00:00Z",
    });

    render(
      <AcceptRiskDialog
        findingId="f1"
        cveId="CVE-2026-1234"
        onAccepted={onAccepted}
      />,
    );

    await user.click(screen.getByLabelText("Accept risk for CVE-2026-1234"));
    await user.type(screen.getByLabelText("Reason"), "Not exploitable");
    await user.click(screen.getByRole("button", { name: "Accept Risk" }));

    expect(createAcceptance).toHaveBeenCalledWith(
      "f1",
      "Not exploitable",
      null,
    );
    expect(onAccepted).toHaveBeenCalled();
  });
});
