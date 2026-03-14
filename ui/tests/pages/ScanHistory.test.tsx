import { render, screen } from "@testing-library/react";
import { ScanHistory } from "@/pages/ScanHistory";

vi.mock("@/lib/api/scans", () => ({
  fetchScans: vi.fn(),
  fetchAgentScans: vi.fn(),
  triggerScan: vi.fn(),
}));

vi.mock("@/lib/api/agents", () => ({
  fetchAgents: vi.fn(),
}));

import { fetchScans } from "@/lib/api/scans";
import { fetchAgents } from "@/lib/api/agents";

const mockPagedScans = { data: [], total: 0, page: 1, page_size: 50 };
const mockPagedAgents = { data: [], total: 0, page: 1, page_size: 200 };

describe("ScanHistory", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchScans).mockResolvedValue(mockPagedScans);
    vi.mocked(fetchAgents).mockResolvedValue(mockPagedAgents);
  });

  it("header container has flex-wrap to prevent mobile overflow", async () => {
    const { container } = render(<ScanHistory />);
    await screen.findByText("Scan History");

    const heading = container.querySelector("h1");
    const headerDiv = heading!.parentElement!;
    expect(headerDiv.className).toContain("flex-wrap");
  });
});
