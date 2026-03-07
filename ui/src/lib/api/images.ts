import { api } from "./client";
import type { ImageResponse, PaginatedResponse } from "./types";

export function fetchImages(params?: {
  agent_id?: string;
  fixable?: boolean;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}) {
  const search = new URLSearchParams();
  if (params?.agent_id) search.set("agent_id", params.agent_id);
  if (params?.fixable) search.set("fixable", "true");
  if (params?.sort_by) search.set("sort_by", params.sort_by);
  if (params?.sort_dir) search.set("sort_dir", params.sort_dir);
  if (params?.page) search.set("page", String(params.page));
  if (params?.page_size) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return api<PaginatedResponse<ImageResponse>>(
    `/api/v1/images${qs ? `?${qs}` : ""}`,
  );
}
