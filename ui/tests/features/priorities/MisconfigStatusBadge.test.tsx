import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MisconfigStatusBadge } from "@/features/priorities/components/MisconfigStatusBadge";

describe("MisconfigStatusBadge", () => {
  it("renders active status with correct styling", () => {
    render(<MisconfigStatusBadge status="active" />);
    const badge = screen.getByText("Active");
    expect(badge).toHaveClass("bg-sky-600/15");
    expect(badge).toHaveClass("text-sky-400");
  });

  it("renders fixed status with correct styling", () => {
    render(<MisconfigStatusBadge status="fixed" />);
    const badge = screen.getByText("Fixed");
    expect(badge).toHaveClass("bg-green-700/15");
    expect(badge).toHaveClass("text-green-400");
  });

  it("renders accepted status with correct styling", () => {
    render(<MisconfigStatusBadge status="accepted" />);
    const badge = screen.getByText("Accepted");
    expect(badge).toHaveClass("bg-violet-600/15");
    expect(badge).toHaveClass("text-violet-400");
  });

  it("renders false_positive status with correct styling", () => {
    render(<MisconfigStatusBadge status="false_positive" />);
    const badge = screen.getByText("False Positive");
    expect(badge).toHaveClass("bg-gray-600/15");
    expect(badge).toHaveClass("text-gray-400");
  });

  it("has border styling", () => {
    render(<MisconfigStatusBadge status="active" />);
    const badge = screen.getByText("Active");
    expect(badge).toHaveClass("border");
    expect(badge).toHaveClass("border-sky-600/30");
  });
});
