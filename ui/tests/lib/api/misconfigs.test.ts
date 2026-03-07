import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  fetchMisconfigs,
  fetchMisconfig,
  updateMisconfig,
  createMisconfigAcceptance,
  revokeMisconfigAcceptance,
} from "@/lib/api/misconfigs";

const mockApiCall = vi.fn();
vi.mock("@/lib/api", () => ({
  api: mockApiCall,
}));

describe("Misconfigs API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("fetchMisconfigs", () => {
    it("calls api with correct endpoint and no params", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchMisconfigs();

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?page=1&page_size=50",
      );
    });

    it("includes severity param when provided", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchMisconfigs({ severity: "HIGH" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?severity=HIGH&page=1&page_size=50",
      );
    });

    it("includes status param when provided", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchMisconfigs({ status: "active" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?status=active&page=1&page_size=50",
      );
    });

    it("includes agent_id param when provided", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchMisconfigs({ agent_id: "abc123" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?agent_id=abc123&page=1&page_size=50",
      );
    });

    it("includes sort params when provided", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchMisconfigs({ sort_by: "first_seen", sort_dir: "desc" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?sort_by=first_seen&sort_dir=desc&page=1&page_size=50",
      );
    });

    it("includes pagination params", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 100,
        page: 2,
        page_size: 25,
      });

      await fetchMisconfigs({ page: 2, page_size: 25 });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs?page=2&page_size=25",
      );
    });

    it("includes multiple params together", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 10,
        page: 1,
        page_size: 50,
      });

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
      const mockMisconfig = {
        id: "misconf-123",
        check_id: "CKV_DOCKER_1",
        severity: "HIGH" as const,
        status: "active" as const,
        container_id: "abc123",
        image_name: "nginx:latest",
        issue: "Exposed port",
        fix: "Use USER directive",
        first_seen: "2026-03-01T10:00:00Z",
      };

      mockApiCall.mockResolvedValue(mockMisconfig);

      const result = await fetchMisconfig("misconf-123");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123",
      );
      expect(result).toEqual(mockMisconfig);
    });
  });

  describe("updateMisconfig", () => {
    it("sends PATCH request with status update", async () => {
      mockApiCall.mockResolvedValue({ id: "misconf-123", status: "fixed" });

      await updateMisconfig("misconf-123", { status: "fixed" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123",
        "PATCH",
        { status: "fixed" },
      );
    });

    it("sends multiple fields in PATCH", async () => {
      mockApiCall.mockResolvedValue({
        id: "misconf-123",
        status: "false_positive",
        checked_at: "2026-03-07T00:00:00Z",
      });

      await updateMisconfig("misconf-123", {
        status: "false_positive",
        checked_at: "2026-03-07T00:00:00Z",
      });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123",
        "PATCH",
        {
          status: "false_positive",
          checked_at: "2026-03-07T00:00:00Z",
        },
      );
    });
  });

  describe("createMisconfigAcceptance", () => {
    it("sends POST request with risk acceptance data", async () => {
      mockApiCall.mockResolvedValue({
        id: "risk-123",
        misconfig_id: "misconf-123",
        note: "Acceptable risk",
      });

      await createMisconfigAcceptance("misconf-123", {
        note: "Acceptable risk",
      });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123/acceptances",
        "POST",
        { note: "Acceptable risk" },
      );
    });

    it("works without note", async () => {
      mockApiCall.mockResolvedValue({
        id: "risk-123",
        misconfig_id: "misconf-123",
        note: "",
      });

      await createMisconfigAcceptance("misconf-123", {});

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123/acceptances",
        "POST",
        {},
      );
    });
  });

  describe("revokeMisconfigAcceptance", () => {
    it("sends DELETE request", async () => {
      mockApiCall.mockResolvedValue({});

      await revokeMisconfigAcceptance("misconf-123");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/misconfigs/misconf-123/acceptances",
        "DELETE",
      );
    });
  });
});
