import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  fetchMisconfigs,
  fetchMisconfig,
  updateMisconfig,
  createMisconfigAcceptance,
  revokeMisconfigAcceptance,
} from "@/lib/api/misconfigs";

const mockApiCall = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", () => ({
  api: mockApiCall,
}));

describe("Misconfigs API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiCall.mockResolvedValue({
      data: [],
      total: 0,
      page: 1,
      page_size: 50,
    });
  });

  describe("fetchMisconfigs", () => {
    it("calls api with correct endpoint and no params when none provided", async () => {
      await fetchMisconfigs();

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/misconfigs");
    });

    it("includes severity param when provided", async () => {
      await fetchMisconfigs({ severity: "HIGH" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?severity=HIGH",
      );
    });

    it("includes status param when provided", async () => {
      await fetchMisconfigs({ status: "active" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?status=active",
      );
    });

    it("includes agent_id param when provided", async () => {
      await fetchMisconfigs({ agent_id: "abc123" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?agent_id=abc123",
      );
    });

    it("includes sort params when provided", async () => {
      await fetchMisconfigs({ sort_by: "first_seen", sort_dir: "desc" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?sort_by=first_seen&sort_dir=desc",
      );
    });

    it("includes pagination params", async () => {
      await fetchMisconfigs({ page: 2, page_size: 25 });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?page=2&page_size=25",
      );
    });

    it("includes multiple params together", async () => {
      await fetchMisconfigs({
        severity: "CRITICAL",
        status: "active",
        agent_id: "prod-01",
        sort_by: "severity",
        sort_dir: "asc",
        page: 1,
        page_size: 20,
      });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?severity=CRITICAL&status=active&agent_id=prod-01&sort_by=severity&sort_dir=asc&page=1&page_size=20",
      );
    });
  });

  describe("fetchMisconfig", () => {
    it("calls api with misconfig id endpoint", async () => {
      mockApiCall.mockResolvedValue({ id: "misconf-123" });

      const result = await fetchMisconfig("misconf-123");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123",
      );
      expect(result).toEqual({ id: "misconf-123" });
    });
  });

  describe("updateMisconfig", () => {
    it("sends PATCH request with status update", async () => {
      mockApiCall.mockResolvedValue({ id: "misconf-123", status: "fixed" });

      await updateMisconfig("misconf-123", "fixed");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123",
        expect.objectContaining({ method: "PATCH" }),
      );
    });

    it("sends false_positive status", async () => {
      mockApiCall.mockResolvedValue({
        id: "misconf-123",
        status: "false_positive",
      });

      await updateMisconfig("misconf-123", "false_positive");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123",
        expect.objectContaining({ method: "PATCH" }),
      );
    });
  });

  describe("createMisconfigAcceptance", () => {
    it("sends POST request with reason", async () => {
      mockApiCall.mockResolvedValue({
        id: "risk-123",
        misconfig_id: "misconf-123",
      });

      await createMisconfigAcceptance("misconf-123", "Acceptable risk");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123/acceptances",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  describe("revokeMisconfigAcceptance", () => {
    it("sends DELETE request", async () => {
      mockApiCall.mockResolvedValue({});

      await revokeMisconfigAcceptance("misconf-123", "acceptance-456");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123/acceptances/acceptance-456",
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });
});
