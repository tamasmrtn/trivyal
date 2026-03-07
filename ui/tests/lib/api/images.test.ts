import { describe, it, expect, beforeEach, vi } from "vitest";
import { fetchImages } from "@/lib/api/images";

const mockApiCall = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", () => ({
  api: mockApiCall,
}));

describe("Images API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiCall.mockResolvedValue({
      data: [],
      total: 0,
      page: 1,
      page_size: 50,
    });
  });

  describe("fetchImages", () => {
    it("calls api with correct endpoint and no extra params when none provided", async () => {
      await fetchImages();

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/images");
    });

    it("includes agent_id param when provided", async () => {
      await fetchImages({ agent_id: "prod-01" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?agent_id=prod-01",
      );
    });

    it("includes fixable param when true", async () => {
      await fetchImages({ fixable: true });

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/images?fixable=true");
    });

    it("does not include fixable param when false", async () => {
      await fetchImages({ fixable: false });

      expect(mockApiCall).toHaveBeenCalledWith("/api/v1/images");
    });

    it("includes sort params when provided", async () => {
      await fetchImages({ sort_by: "fixable_cves", sort_dir: "desc" });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?sort_by=fixable_cves&sort_dir=desc",
      );
    });

    it("includes pagination params", async () => {
      await fetchImages({ page: 2, page_size: 25 });

      expect(mockApiCall).toHaveBeenCalledWith(
        "/api/v1/images?page=2&page_size=25",
      );
    });

    it("includes multiple params together", async () => {
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
