import { render, screen } from "@testing-library/react";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import type { Severity } from "@/lib/api/types";

describe("SeverityBadge", () => {
  const cases: { severity: Severity; colorClass: string }[] = [
    { severity: "CRITICAL", colorClass: "bg-red-600" },
    { severity: "HIGH", colorClass: "bg-orange-500" },
    { severity: "MEDIUM", colorClass: "bg-yellow-500" },
    { severity: "LOW", colorClass: "bg-blue-500" },
    { severity: "UNKNOWN", colorClass: "bg-gray-500" },
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
