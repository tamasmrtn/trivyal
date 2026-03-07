import { describe, it, expect, beforeEach, vi } from "vitest";
import { fetchImages } from "@/lib/api/images";

const mockApiCall = vi.fn();
vi.mock("@/lib/api", () => ({
  api: mockApiCall,
}));

describe("Images API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("fetchImages", () => {
    it("calls api with correct endpoint and default params", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchImages();

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?page=1&page_size=50",
      );
    });

    it("includes agent_id param when provided", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchImages({ agent_id: "prod-01" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?agent_id=prod-01&page=1&page_size=50",
      );
    });

    it("includes fixable param when true", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchImages({ fixable: true });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?fixable=true&page=1&page_size=50",
      );
    });

    it("includes fixable param when false", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchImages({ fixable: false });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?fixable=false&page=1&page_size=50",
      );
    });

    it("includes sort params when provided", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 0,
        page: 1,
        page_size: 50,
      });

      await fetchImages({ sort_by: "fixable_cves", sort_dir: "desc" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?sort_by=fixable_cves&sort_dir=desc&page=1&page_size=50",
      );
    });

    it("includes pagination params", async () => {
      mockApiCall.mockResolvedValue({
        data: [],
        total: 100,
        page: 2,
        page_size: 25,
      });

      await fetchImages({ page: 2, page_size: 25 });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?page=2&page_size=25",
      );
    });

    it("includes multiple params together", async () => {
      mockApiCall.mockResolvedValue({
        data: [
          {
            name: "nginx",
            tag: "latest",
            fixable_cves: 5,
            total_cves: 10,
            severity_counts: { critical: 1, high: 2, medium: 2, low: 5 },
            agents: [{ agent_id: "prod-01", name: "prod-01" }],
            last_scanned: "2026-03-07T10:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      });

      await fetchImages({
        agent_id: "prod-01",
        fixable: true,
        sort_by: "fixable_cves",
        sort_dir: "desc",
        page: 1,
        page_size: 20,
      });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?agent_id=prod-01&fixable=true&sort_by=fixable_cves&sort_dir=desc&page=1&page_size=20",
      );
    });
  });
});
