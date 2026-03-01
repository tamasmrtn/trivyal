import { api } from "./client";
import type { SettingsResponse, WebhookType } from "./types";

export function fetchSettings() {
  return api<SettingsResponse>("/api/v1/settings");
}

export function updateSettings(body: {
  webhook_url?: string | null;
  webhook_type?: WebhookType;
  notify_on_critical?: boolean;
  notify_on_high?: boolean;
}) {
  return api<SettingsResponse>("/api/v1/settings", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}
