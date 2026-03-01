import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/features/agents/components/StatusBadge";
import type { AgentStatus } from "@/lib/api/types";

describe("StatusBadge", () => {
  const cases: { status: AgentStatus; label: string }[] = [
    { status: "online", label: "Online" },
    { status: "offline", label: "Offline" },
    { status: "scanning", label: "Scanning" },
  ];

  it.each(cases)("renders $label for $status status", ({ status, label }) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});
