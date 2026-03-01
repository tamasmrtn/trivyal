import { render, screen } from "@testing-library/react";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import type { Severity } from "@/lib/api/types";

describe("SeverityBadge", () => {
  const cases: { severity: Severity; colorClass: string }[] = [
    { severity: "CRITICAL", colorClass: "bg-red-600" },
    { severity: "HIGH", colorClass: "bg-orange-600" },
    { severity: "MEDIUM", colorClass: "bg-amber-600" },
    { severity: "LOW", colorClass: "bg-blue-600" },
    { severity: "UNKNOWN", colorClass: "bg-gray-600" },
  ];

  it.each(cases)(
    "renders $severity with correct text and color",
    ({ severity, colorClass }) => {
      render(<SeverityBadge severity={severity} />);
      const badge = screen.getByText(severity);
      expect(badge).toBeInTheDocument();
      expect(badge.className).toContain(colorClass);
    },
  );
});
