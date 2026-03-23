import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useScans } from "@/features/scans/hooks/useScans";

vi.mock("@/lib/api/scans", () => ({
  fetchScans: vi.fn(),
  fetchAgentScans: vi.fn(),
}));

import { fetchScans, fetchAgentScans } from "@/lib/api/scans";

const mockResponse = {
  data: [
    {
      id: "scan-1",
      agent_id: "agent-1",
      image_name: "nginx:latest",
      started_at: "2026-03-01T00:00:00Z",
      finished_at: "2026-03-01T00:01:00Z",
      vulnerability_count: 5,
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
};

describe("useScans hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns initial loading state", () => {
    vi.mocked(fetchScans).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useScans());

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it("loads scans successfully without agentId", async () => {
    vi.mocked(fetchScans).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useScans());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(fetchScans).toHaveBeenCalled();
    expect(fetchAgentScans).not.toHaveBeenCalled();
    expect(result.current.data).toEqual(mockResponse.data);
    expect(result.current.total).toBe(1);
  });

  it("loads agent scans when agentId is provided", async () => {
    vi.mocked(fetchAgentScans).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useScans({ agentId: "agent-1" }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(fetchAgentScans).toHaveBeenCalledWith("agent-1", {
      page: undefined,
      page_size: undefined,
    });
    expect(fetchScans).not.toHaveBeenCalled();
  });

  it("handles fetch errors", async () => {
    vi.mocked(fetchScans).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useScans());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.data).toEqual([]);
  });

  it("re-fetches when agentId changes", async () => {
    vi.mocked(fetchScans).mockResolvedValue(mockResponse);
    vi.mocked(fetchAgentScans).mockResolvedValue(mockResponse);

    const { rerender } = renderHook(
      ({ agentId }: { agentId?: string }) => useScans({ agentId }),
      { initialProps: { agentId: undefined } },
    );

    await waitFor(() => {
      expect(fetchScans).toHaveBeenCalledTimes(1);
    });

    rerender({ agentId: "agent-1" });

    await waitFor(() => {
      expect(fetchAgentScans).toHaveBeenCalledTimes(1);
    });
  });

  it("provides refetch function", async () => {
    vi.mocked(fetchScans).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useScans());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.refetch).toBeDefined();

    result.current.refetch();

    await waitFor(() => {
      expect(fetchScans).toHaveBeenCalledTimes(2);
    });
  });
});
