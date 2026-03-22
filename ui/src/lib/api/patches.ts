import { api } from "./client";
import { useAuthStore } from "@/store/auth";
import type {
  PaginatedResponse,
  PatchResponse,
  PatchSummary,
  RestartResponse,
} from "./types";

export function fetchPatches(params?: {
  status?: string;
  agent_id?: string;
  page?: number;
  page_size?: number;
}) {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.agent_id) search.set("agent_id", params.agent_id);
  if (params?.page) search.set("page", String(params.page));
  if (params?.page_size) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return api<PaginatedResponse<PatchResponse>>(
    `/api/v1/patches${qs ? `?${qs}` : ""}`,
  );
}

export function fetchPatch(id: string) {
  return api<PatchResponse>(`/api/v1/patches/${id}`);
}

export function createPatch(body: {
  agent_id: string;
  container_id: string;
  image_name: string;
}) {
  return api<PatchResponse>("/api/v1/patches", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function triggerRestart(patchId: string) {
  return api<RestartResponse>(`/api/v1/patches/${patchId}/restart`, {
    method: "POST",
  });
}

export function fetchPatchSummary() {
  return api<PatchSummary>("/api/v1/dashboard/patch-summary");
}

export function subscribePatchLogs(
  patchId: string,
  onLine: (line: string) => void,
  onDone: () => void,
) {
  const token = useAuthStore.getState().token;
  const controller = new AbortController();

  fetch(`/api/v1/patches/${patchId}/logs`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal: controller.signal,
  })
    .then(async (response) => {
      const reader = response.body?.getReader();
      if (!reader) {
        onDone();
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            onLine(line.slice(6));
          }
        }
      }
      onDone();
    })
    .catch(() => {
      onDone();
    });

  return () => controller.abort();
}
