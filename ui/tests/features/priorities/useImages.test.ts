import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useImages } from "@/features/priorities/hooks/useImages";

vi.mock("@/lib/api/images", () => ({
  fetchImages: vi.fn(),
}));

import { fetchImages } from "@/lib/api/images";

const mockImage = {
  name: "nginx",
  tag: "latest",
  fixable_cves: 5,
  total_cves: 10,
  severity_counts: {
    critical: 1,
    high: 2,
    medium: 2,
    low: 5,
  },
  agents: [
    {
      agent_id: "prod-01",
      name: "prod-01",
    },
  ],
  last_scanned: "2026-03-07T10:00:00Z",
};

const mockResponse = {
  data: [mockImage],
  total: 1,
  page: 1,
  page_size: 50,
};

describe("useImages hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns initial loading state", () => {
    vi.mocked(fetchImages).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useImages());

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it("loads images successfully", async () => {
    vi.mocked(fetchImages).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useImages());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual([mockImage]);
    expect(result.current.total).toBe(1);
    expect(result.current.error).toBeNull();
  });

  it("handles fetch errors", async () => {
    const error = new Error("Fetch failed");
    vi.mocked(fetchImages).mockRejectedValue(error);

    const { result } = renderHook(() => useImages());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Fetch failed");
    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
  });

  it("passes agent_id filter to API", async () => {
    vi.mocked(fetchImages).mockResolvedValue(mockResponse);

    renderHook(() =>
      useImages({
        agent_id: "prod-01",
      }),
    );

    await waitFor(() => {
      expect(fetchImages).toHaveBeenCalledWith(
        expect.objectContaining({ agent_id: "prod-01" }),
      );
    });
  });

  it("passes fixable filter to API", async () => {
    vi.mocked(fetchImages).mockResolvedValue(mockResponse);

    renderHook(() =>
      useImages({
        fixable: true,
      }),
    );

    await waitFor(() => {
      expect(fetchImages).toHaveBeenCalledWith(
        expect.objectContaining({ fixable: true }),
      );
    });
  });

  it("passes sort params to API", async () => {
    vi.mocked(fetchImages).mockResolvedValue(mockResponse);

    renderHook(() =>
      useImages({
        sort_by: "fixable_cves",
        sort_dir: "desc",
      }),
    );

    await waitFor(() => {
      expect(fetchImages).toHaveBeenCalledWith(
        expect.objectContaining({
          sort_by: "fixable_cves",
          sort_dir: "desc",
        }),
      );
    });
  });

  it("passes pagination params to API", async () => {
    vi.mocked(fetchImages).mockResolvedValue({
      ...mockResponse,
      page: 2,
      page_size: 25,
    });

    renderHook(() =>
      useImages({
        page: 2,
        page_size: 25,
      }),
    );

    await waitFor(() => {
      expect(fetchImages).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
          page_size: 25,
        }),
      );
    });
  });

  it("re-fetches when options change", async () => {
    vi.mocked(fetchImages).mockResolvedValue(mockResponse);

    const { rerender } = renderHook(
      ({ fixable }: { fixable?: boolean }) => useImages({ fixable }),
      {
        initialProps: { fixable: undefined },
      },
    );

    await waitFor(() => {
      expect(fetchImages).toHaveBeenCalledTimes(1);
    });

    rerender({ fixable: true });

    await waitFor(() => {
      expect(fetchImages).toHaveBeenCalledTimes(2);
      expect(fetchImages).toHaveBeenLastCalledWith(
        expect.objectContaining({ fixable: true }),
      );
    });
  });

  it("provides refetch function", async () => {
    vi.mocked(fetchImages).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useImages());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.refetch).toBeDefined();

    result.current.refetch();

    await waitFor(() => {
      expect(fetchImages).toHaveBeenCalledTimes(2);
    });
  });
});
