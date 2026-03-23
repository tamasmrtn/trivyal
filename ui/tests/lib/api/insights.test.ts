import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  fetchInsightsSummary,
  fetchInsightsTrend,
  fetchAgentsTrend,
  fetchTopCves,
} from "@/lib/api/insights";

const mockApiCall = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", () => ({
  api: mockApiCall,
}));

describe("Insights API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiCall.mockResolvedValue({});
  });

  describe("fetchInsightsSummary", () => {
    it("includes window param", async () => {
      await fetchInsightsSummary(7);

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/summary?window=7",
      );
    });

    it("includes fixable param when true", async () => {
      await fetchInsightsSummary(30, true);

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/summary?window=30&fixable=true",
      );
    });

    it("includes agent_id param when provided", async () => {
      await fetchInsightsSummary(7, undefined, "agent-1");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/summary?window=7&agent_id=agent-1",
      );
    });

    it("includes all params together", async () => {
      await fetchInsightsSummary(14, true, "agent-1");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/summary?window=14&fixable=true&agent_id=agent-1",
      );
    });
  });

  describe("fetchInsightsTrend", () => {
    it("includes window param", async () => {
      await fetchInsightsTrend(7);

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/trend?window=7",
      );
    });

    it("includes all params together", async () => {
      await fetchInsightsTrend(30, true, "agent-2");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/trend?window=30&fixable=true&agent_id=agent-2",
      );
    });
  });

  describe("fetchAgentsTrend", () => {
    it("includes window param", async () => {
      await fetchAgentsTrend(7);

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/agents/trend?window=7",
      );
    });

    it("includes all params together", async () => {
      await fetchAgentsTrend(14, true, "agent-3");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/agents/trend?window=14&fixable=true&agent_id=agent-3",
      );
    });
  });

  describe("fetchTopCves", () => {
    it("includes window param", async () => {
      await fetchTopCves(7);

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/top-cves?window=7",
      );
    });

    it("includes all params together", async () => {
      await fetchTopCves(90, true, "agent-4");

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/insights/top-cves?window=90&fixable=true&agent_id=agent-4",
      );
    });
  });
});
