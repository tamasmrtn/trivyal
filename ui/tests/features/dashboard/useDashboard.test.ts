import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useDashboard } from "@/features/dashboard/hooks/useDashboard";

vi.mock("@/lib/api/dashboard", () => ({
  fetchDashboardSummary: vi.fn(),
}));

import { fetchDashboardSummary } from "@/lib/api/dashboard";

const mockSummary = {
  severity_counts: {
    critical: 1,
    high: 2,
    medium: 3,
    low: 4,
    unknown: 0,
  },
  agent_status_counts: { online: 1, offline: 0, scanning: 0 },
  total_findings: 10,
  total_agents: 1,
  misconfig: { total_active: 2 },
  fixable_cves: 5,
};

describe("useDashboard hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns initial loading state", () => {
    vi.mocked(fetchDashboardSummary).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useDashboard());

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("returns data on success", async () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue(mockSummary);

    const { result } = renderHook(() => useDashboard());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockSummary);
    expect(result.current.error).toBeNull();
  });

  it("returns error on failure", async () => {
    vi.mocked(fetchDashboardSummary).mockRejectedValue(
      new Error("Network error"),
    );

    const { result } = renderHook(() => useDashboard());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.data).toBeNull();
  });

  it("returns fallback error message for non-Error rejections", async () => {
    vi.mocked(fetchDashboardSummary).mockRejectedValue("something went wrong");

    const { result } = renderHook(() => useDashboard());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to load dashboard");
  });

  it("passes fixable param to fetchDashboardSummary", async () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue(mockSummary);

    renderHook(() => useDashboard(true));

    await waitFor(() => {
      expect(fetchDashboardSummary).toHaveBeenCalledWith(true);
    });
  });

  it("re-fetches when fixable changes", async () => {
    vi.mocked(fetchDashboardSummary).mockResolvedValue(mockSummary);

    const { rerender } = renderHook(
      ({ fixable }: { fixable?: boolean }) => useDashboard(fixable),
      { initialProps: { fixable: undefined } },
    );

    await waitFor(() => {
      expect(fetchDashboardSummary).toHaveBeenCalledTimes(1);
    });

    rerender({ fixable: true });

    await waitFor(() => {
      expect(fetchDashboardSummary).toHaveBeenCalledTimes(2);
      expect(fetchDashboardSummary).toHaveBeenLastCalledWith(true);
    });
  });
});
