import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  fetchFindings,
  fetchFinding,
  updateFinding,
  fetchAcceptances,
  createAcceptance,
  revokeAcceptance,
} from "@/lib/api/findings";

const mockApiCall = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", () => ({
  api: mockApiCall,
}));

describe("Findings API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiCall.mockResolvedValue({
      data: [],
      total: 0,
      page: 1,
      page_size: 50,
    });
  });

  describe("fetchFindings", () => {
    it("calls api with correct endpoint and no params when none provided", async () => {
      await fetchFindings();

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/findings");
    });

    it("includes severity param when provided", async () => {
      await fetchFindings({ severity: "CRITICAL" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?severity=CRITICAL",
      );
    });

    it("includes status param when provided", async () => {
      await fetchFindings({ status: "active" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?status=active",
      );
    });

    it("includes agent_id param when provided", async () => {
      await fetchFindings({ agent_id: "agent-1" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?agent_id=agent-1",
      );
    });

    it("includes cve_id param when provided", async () => {
      await fetchFindings({ cve_id: "CVE-2026-1234" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?cve_id=CVE-2026-1234",
      );
    });

    it("includes package param when provided", async () => {
      await fetchFindings({ package: "openssl" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?package=openssl",
      );
    });

    it("includes container_id param when provided", async () => {
      await fetchFindings({ container_id: "abc123" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?container_id=abc123",
      );
    });

    it("includes image_name param when provided", async () => {
      await fetchFindings({ image_name: "nginx" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?image_name=nginx",
      );
    });

    it("includes image_tag param when provided", async () => {
      await fetchFindings({ image_tag: "latest" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?image_tag=latest",
      );
    });

    it("includes fixable param when true", async () => {
      await fetchFindings({ fixable: true });

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/findings?fixable=true");
    });

    it("excludes fixable param when false", async () => {
      await fetchFindings({ fixable: false });

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/findings");
    });

    it("includes sort params when provided", async () => {
      await fetchFindings({ sort_by: "severity", sort_dir: "desc" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?sort_by=severity&sort_dir=desc",
      );
    });

    it("includes pagination params", async () => {
      await fetchFindings({ page: 2, page_size: 25 });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?page=2&page_size=25",
      );
    });

    it("includes multiple params together", async () => {
      await fetchFindings({
        severity: "HIGH",
        status: "active",
        agent_id: "prod-01",
        image_name: "nginx",
        fixable: true,
        sort_by: "first_seen",
        sort_dir: "asc",
        page: 1,
        page_size: 20,
      });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings?severity=HIGH&status=active&agent_id=prod-01&image_name=nginx&fixable=true&sort_by=first_seen&sort_dir=asc&page=1&page_size=20",
      );
    });
  });

  describe("fetchFinding", () => {
    it("calls api with finding id endpoint", async () => {
      mockApiCall.mockResolvedValue({ id: "finding-123" });

      const result = await fetchFinding("finding-123");

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/findings/finding-123");
      expect(result).toEqual({ id: "finding-123" });
    });
  });

  describe("updateFinding", () => {
    it("sends PATCH request with status", async () => {
      mockApiCall.mockResolvedValue({ id: "f1", status: "fixed" });

      await updateFinding("f1", "fixed");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings/f1",
        expect.objectContaining({ method: "PATCH" }),
      );
    });
  });

  describe("fetchAcceptances", () => {
    it("calls api with acceptances endpoint", async () => {
      mockApiCall.mockResolvedValue([]);

      await fetchAcceptances("f1");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings/f1/acceptances",
      );
    });
  });

  describe("createAcceptance", () => {
    it("sends POST request with reason and expires_at", async () => {
      mockApiCall.mockResolvedValue({ id: "acc-1" });

      await createAcceptance("f1", "Acceptable risk", "2026-12-31");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings/f1/acceptances",
        expect.objectContaining({ method: "POST" }),
      );
    });

    it("sends null expires_at when not provided", async () => {
      mockApiCall.mockResolvedValue({ id: "acc-1" });

      await createAcceptance("f1", "Acceptable risk");

      const call = mockApiCall.mock.calls[0];
      const body = JSON.parse(call[1].body);
      expect(body.expires_at).toBeNull();
    });
  });

  describe("revokeAcceptance", () => {
    it("sends DELETE request to correct path", async () => {
      mockApiCall.mockResolvedValue({});

      await revokeAcceptance("f1", "acc-1");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/findings/f1/acceptances/acc-1",
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });
});
