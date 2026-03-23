import { describe, it, expect, beforeEach, vi } from "vitest";
import { fetchDashboardSummary } from "@/lib/api/dashboard";

const mockApiCall = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", () => ({
  api: mockApiCall,
}));

describe("Dashboard API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiCall.mockResolvedValue({});
  });

  describe("fetchDashboardSummary", () => {
    it("calls api with no query string when fixable is undefined", async () => {
      await fetchDashboardSummary();

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/dashboard/summary");
    });

    it("calls api with no query string when fixable is false", async () => {
      await fetchDashboardSummary(false);

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/dashboard/summary");
    });

    it("includes fixable query param when true", async () => {
      await fetchDashboardSummary(true);

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/dashboard/summary?fixable=true",
      );
    });
  });
});
