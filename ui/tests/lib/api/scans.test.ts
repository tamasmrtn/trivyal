import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  fetchScans,
  fetchAgentScans,
  fetchScan,
  triggerScan,
} from "@/lib/api/scans";

const mockApiCall = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", () => ({
  api: mockApiCall,
}));

describe("Scans API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiCall.mockResolvedValue({
      data: [],
      total: 0,
      page: 1,
      page_size: 50,
    });
  });

  describe("fetchScans", () => {
    it("calls api with correct endpoint and no params when none provided", async () => {
      await fetchScans();

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/scans");
    });

    it("includes page param when provided", async () => {
      await fetchScans({ page: 2 });

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/scans?page=2");
    });

    it("includes page_size param when provided", async () => {
      await fetchScans({ page_size: 25 });

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/scans?page_size=25");
    });

    it("includes both pagination params", async () => {
      await fetchScans({ page: 3, page_size: 10 });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/scans?page=3&page_size=10",
      );
    });
  });

  describe("fetchAgentScans", () => {
    it("calls api with agent-specific endpoint", async () => {
      await fetchAgentScans("agent-1");

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/agents/agent-1/scans");
    });

    it("includes pagination params", async () => {
      await fetchAgentScans("agent-1", { page: 2, page_size: 25 });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/agents/agent-1/scans?page=2&page_size=25",
      );
    });
  });

  describe("fetchScan", () => {
    it("calls api with scan id endpoint", async () => {
      mockApiCall.mockResolvedValue({ id: "scan-123" });

      const result = await fetchScan("scan-123");

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/scans/scan-123");
      expect(result).toEqual({ id: "scan-123" });
    });
  });

  describe("triggerScan", () => {
    it("sends POST to agent scans endpoint", async () => {
      mockApiCall.mockResolvedValue({ job_id: "job-1" });

      const result = await triggerScan("agent-1");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/agents/agent-1/scans",
        expect.objectContaining({ method: "POST" }),
      );
      expect(result).toEqual({ job_id: "job-1" });
    });
  });
});
