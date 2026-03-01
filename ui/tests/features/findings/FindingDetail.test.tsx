import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { FindingDetail } from "@/pages/FindingDetail";
import {
  fetchFinding,
  fetchAcceptances,
  updateFinding,
  revokeAcceptance,
  createAcceptance,
} from "@/lib/api/findings";
import type { FindingResponse } from "@/lib/api/types";
import type { RiskAcceptanceResponse } from "@/lib/api/findings";

vi.mock("@/lib/api/findings", () => ({
  fetchFinding: vi.fn(),
  fetchAcceptances: vi.fn(),
  updateFinding: vi.fn(),
  revokeAcceptance: vi.fn(),
  createAcceptance: vi.fn(),
}));

const mockFinding: FindingResponse = {
  id: "f1",
  scan_result_id: "sr1",
  cve_id: "CVE-2026-1234",
  package_name: "openssl",
  installed_version: "1.1.1",
  fixed_version: "1.1.2",
  severity: "CRITICAL",
  status: "active",
  first_seen: "2026-02-01T00:00:00Z",
  last_seen: "2026-03-01T00:00:00Z",
};

const mockAcceptance: RiskAcceptanceResponse = {
  id: "a1",
  finding_id: "f1",
  reason: "Not exploitable in our environment",
  accepted_by: "admin",
  expires_at: null,
  created_at: "2026-03-01T00:00:00Z",
};

function renderDetail(id = "f1") {
  return render(
    <MemoryRouter initialEntries={[`/findings/${id}`]}>
      <Routes>
        <Route path="/findings/:id" element={<FindingDetail />} />
        <Route path="/findings" element={<div>Findings List</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("FindingDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchFinding).mockResolvedValue(mockFinding);
    vi.mocked(fetchAcceptances).mockResolvedValue([]);
  });

  it("shows loading state initially", () => {
    vi.mocked(fetchFinding).mockReturnValue(new Promise(() => {}));
    vi.mocked(fetchAcceptances).mockReturnValue(new Promise(() => {}));
    renderDetail();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows error state when fetch fails", async () => {
    vi.mocked(fetchFinding).mockRejectedValue(new Error("Not found"));
    renderDetail();
    expect(await screen.findByText("Not found")).toBeInTheDocument();
  });

  it("renders CVE ID as page heading", async () => {
    renderDetail();
    expect(
      await screen.findByRole("heading", { name: "CVE-2026-1234" }),
    ).toBeInTheDocument();
  });

  it("renders all finding detail fields", async () => {
    renderDetail();
    await screen.findByRole("heading", { name: "CVE-2026-1234" });
    expect(screen.getByText("openssl")).toBeInTheDocument();
    expect(screen.getByText("1.1.1")).toBeInTheDocument();
    expect(screen.getByText("1.1.2")).toBeInTheDocument();
    expect(screen.getByText("sr1")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders back link to findings list", async () => {
    renderDetail();
    await screen.findByRole("heading", { name: "CVE-2026-1234" });
    expect(
      screen.getByRole("link", { name: /back to findings/i }),
    ).toHaveAttribute("href", "/findings");
  });

  it("navigates back when back link is clicked", async () => {
    const user = userEvent.setup();
    renderDetail();
    await screen.findByRole("heading", { name: "CVE-2026-1234" });
    await user.click(screen.getByRole("link", { name: /back to findings/i }));
    expect(screen.getByText("Findings List")).toBeInTheDocument();
  });

  describe("actions for active finding", () => {
    it("shows accept risk and false positive buttons", async () => {
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });
      expect(
        screen.getByRole("button", { name: /accept risk/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /mark as false positive/i }),
      ).toBeInTheDocument();
    });

    it("calls updateFinding with false_positive on button click", async () => {
      const user = userEvent.setup();
      vi.mocked(updateFinding).mockResolvedValue({
        ...mockFinding,
        status: "false_positive",
      });
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });
      await user.click(
        screen.getByRole("button", { name: /mark as false positive/i }),
      );
      expect(updateFinding).toHaveBeenCalledWith("f1", "false_positive");
    });
  });

  describe("actions for false_positive finding", () => {
    it("shows mark as active button only", async () => {
      vi.mocked(fetchFinding).mockResolvedValue({
        ...mockFinding,
        status: "false_positive",
      });
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });
      expect(
        screen.getByRole("button", { name: /mark as active/i }),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /mark as false positive/i }),
      ).not.toBeInTheDocument();
    });

    it("calls updateFinding with active on button click", async () => {
      const user = userEvent.setup();
      vi.mocked(fetchFinding).mockResolvedValue({
        ...mockFinding,
        status: "false_positive",
      });
      vi.mocked(updateFinding).mockResolvedValue(mockFinding);
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });
      await user.click(screen.getByRole("button", { name: /mark as active/i }));
      expect(updateFinding).toHaveBeenCalledWith("f1", "active");
    });
  });

  describe("actions for fixed finding", () => {
    it("shows no action buttons", async () => {
      vi.mocked(fetchFinding).mockResolvedValue({
        ...mockFinding,
        status: "fixed",
      });
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });
      expect(
        screen.queryByRole("button", { name: /accept risk/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /mark as false positive/i }),
      ).not.toBeInTheDocument();
    });
  });

  describe("risk acceptances section", () => {
    it("shows empty state when no acceptances", async () => {
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });
      expect(
        screen.getByText(/no risk acceptances recorded/i),
      ).toBeInTheDocument();
    });

    it("renders acceptances in a table", async () => {
      vi.mocked(fetchAcceptances).mockResolvedValue([mockAcceptance]);
      renderDetail();
      await screen.findByText("Not exploitable in our environment");
      expect(screen.getByText("admin")).toBeInTheDocument();
    });

    it("calls revokeAcceptance when revoke button is clicked", async () => {
      const user = userEvent.setup();
      vi.mocked(fetchAcceptances).mockResolvedValue([mockAcceptance]);
      vi.mocked(revokeAcceptance).mockResolvedValue(undefined);
      renderDetail();
      await screen.findByText("Not exploitable in our environment");
      await user.click(screen.getByLabelText("Revoke acceptance"));
      expect(revokeAcceptance).toHaveBeenCalledWith("f1", "a1");
    });

    it("opens accept risk dialog via labeled button", async () => {
      const user = userEvent.setup();
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });
      await user.click(screen.getByRole("button", { name: /accept risk/i }));
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByLabelText("Reason")).toBeInTheDocument();
    });

    it("calls createAcceptance and refetches on submission", async () => {
      const user = userEvent.setup();
      vi.mocked(createAcceptance).mockResolvedValue(mockAcceptance);
      vi.mocked(fetchAcceptances)
        .mockResolvedValueOnce([])
        .mockResolvedValue([mockAcceptance]);
      renderDetail();
      await screen.findByRole("heading", { name: "CVE-2026-1234" });

      await user.click(screen.getByRole("button", { name: /accept risk/i }));
      await user.type(screen.getByLabelText("Reason"), "Not exploitable");
      await user.click(screen.getByRole("button", { name: "Accept Risk" }));

      expect(createAcceptance).toHaveBeenCalledWith(
        "f1",
        "Not exploitable",
        null,
      );
    });
  });
});
