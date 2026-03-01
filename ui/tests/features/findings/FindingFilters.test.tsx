import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FindingFilters } from "@/features/findings/components/FindingFilters";

describe("FindingFilters", () => {
  it("renders severity and status selects", () => {
    render(
      <FindingFilters
        severity={undefined}
        status={undefined}
        onSeverityChange={vi.fn()}
        onStatusChange={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Filter by severity")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by status")).toBeInTheDocument();
  });

  it("calls onSeverityChange when selecting a severity", async () => {
    const onSeverityChange = vi.fn();
    const user = userEvent.setup();

    render(
      <FindingFilters
        severity={undefined}
        status={undefined}
        onSeverityChange={onSeverityChange}
        onStatusChange={vi.fn()}
      />,
    );

    await user.selectOptions(
      screen.getByLabelText("Filter by severity"),
      "CRITICAL",
    );
    expect(onSeverityChange).toHaveBeenCalledWith("CRITICAL");
  });

  it("calls onStatusChange when selecting a status", async () => {
    const onStatusChange = vi.fn();
    const user = userEvent.setup();

    render(
      <FindingFilters
        severity={undefined}
        status={undefined}
        onSeverityChange={vi.fn()}
        onStatusChange={onStatusChange}
      />,
    );

    await user.selectOptions(
      screen.getByLabelText("Filter by status"),
      "fixed",
    );
    expect(onStatusChange).toHaveBeenCalledWith("fixed");
  });

  it("calls handler with undefined when clearing filter", async () => {
    const onSeverityChange = vi.fn();
    const user = userEvent.setup();

    render(
      <FindingFilters
        severity="CRITICAL"
        status={undefined}
        onSeverityChange={onSeverityChange}
        onStatusChange={vi.fn()}
      />,
    );

    await user.selectOptions(screen.getByLabelText("Filter by severity"), "");
    expect(onSeverityChange).toHaveBeenCalledWith(undefined);
  });
});
