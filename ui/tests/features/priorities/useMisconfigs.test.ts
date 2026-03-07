import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useMisconfigs } from "@/features/priorities/hooks/useMisconfigs";

vi.mock("@/lib/api/misconfigs", () => ({
  fetchMisconfigs: vi.fn(),
}));

import { fetchMisconfigs } from "@/lib/api/misconfigs";

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

const mockResponse = {
  data: [mockMisconfig],
  total: 1,
  page: 1,
  page_size: 50,
};

describe("useMisconfigs hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns initial loading state", () => {
    vi.mocked(fetchMisconfigs).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useMisconfigs());

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it("loads misconfigs successfully", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useMisconfigs());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual([mockMisconfig]);
    expect(result.current.total).toBe(1);
    expect(result.current.error).toBeNull();
  });

  it("handles fetch errors", async () => {
    const error = new Error("Fetch failed");
    vi.mocked(fetchMisconfigs).mockRejectedValue(error);

    const { result } = renderHook(() => useMisconfigs());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Fetch failed");
    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
  });

  it("passes severity filter to API", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue(mockResponse);

    renderHook(() =>
      useMisconfigs({
        severity: "CRITICAL",
      }),
    );

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledWith(
        expect.objectContaining({ severity: "CRITICAL" }),
      );
    });
  });

  it("passes status filter to API", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue(mockResponse);

    renderHook(() =>
      useMisconfigs({
        status: "fixed",
      }),
    );

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledWith(
        expect.objectContaining({ status: "fixed" }),
      );
    });
  });

  it("passes agent_id filter to API", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue(mockResponse);

    renderHook(() =>
      useMisconfigs({
        agent_id: "prod-01",
      }),
    );

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledWith(
        expect.objectContaining({ agent_id: "prod-01" }),
      );
    });
  });

  it("passes sort params to API", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue(mockResponse);

    renderHook(() =>
      useMisconfigs({
        sort_by: "severity",
        sort_dir: "asc",
      }),
    );

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledWith(
        expect.objectContaining({
          sort_by: "severity",
          sort_dir: "asc",
        }),
      );
    });
  });

  it("passes pagination params to API", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue({
      ...mockResponse,
      page: 2,
      page_size: 25,
    });

    renderHook(() =>
      useMisconfigs({
        page: 2,
        page_size: 25,
      }),
    );

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
          page_size: 25,
        }),
      );
    });
  });

  it("re-fetches when options change", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue(mockResponse);

    const { rerender } = renderHook(
      ({ severity }: { severity?: string }) => useMisconfigs({ severity }),
      {
        initialProps: { severity: undefined },
      },
    );

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledTimes(1);
    });

    rerender({ severity: "CRITICAL" });

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledTimes(2);
      expect(fetchMisconfigs).toHaveBeenLastCalledWith(
        expect.objectContaining({ severity: "CRITICAL" }),
      );
    });
  });

  it("provides refetch function", async () => {
    vi.mocked(fetchMisconfigs).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useMisconfigs());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.refetch).toBeDefined();

    result.current.refetch();

    await waitFor(() => {
      expect(fetchMisconfigs).toHaveBeenCalledTimes(2);
    });
  });
});
