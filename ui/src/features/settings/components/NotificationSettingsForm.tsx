import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { updateSettings } from "@/lib/api/settings";
import type { SettingsResponse, WebhookType } from "@/lib/api/types";

interface NotificationSettingsFormProps {
  initial: SettingsResponse;
  onSaved: () => void;
}

const WEBHOOK_TYPES: { value: string; label: string }[] = [
  { value: "", label: "None / Generic" },
  { value: "slack", label: "Slack" },
  { value: "discord", label: "Discord" },
  { value: "ntfy", label: "Ntfy" },
];

export function NotificationSettingsForm({
  initial,
  onSaved,
}: NotificationSettingsFormProps) {
  const [webhookUrl, setWebhookUrl] = useState(initial.webhook_url ?? "");
  const [webhookType, setWebhookType] = useState<string>(
    initial.webhook_type ?? "",
  );
  const [notifyOnCritical, setNotifyOnCritical] = useState(
    initial.notify_on_critical,
  );
  const [notifyOnHigh, setNotifyOnHigh] = useState(initial.notify_on_high);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      await updateSettings({
        webhook_url: webhookUrl.trim() || null,
        webhook_type: (webhookType || null) as WebhookType,
        notify_on_critical: notifyOnCritical,
        notify_on_high: notifyOnHigh,
      });
      setSaved(true);
      onSaved();
      setTimeout(() => setSaved(false), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div>
          <label
            htmlFor="webhook-url"
            className="mb-2 block text-sm font-medium"
          >
            Webhook URL
          </label>
          <Input
            id="webhook-url"
            type="url"
            placeholder="https://hooks.slack.com/..."
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            disabled={saving}
          />
          <p className="text-muted-foreground mt-1 text-xs">
            Leave blank to disable notifications.
          </p>
        </div>

        <div>
          <label
            htmlFor="webhook-type"
            className="mb-2 block text-sm font-medium"
          >
            Webhook type
          </label>
          <select
            id="webhook-type"
            value={webhookType}
            onChange={(e) => setWebhookType(e.target.value)}
            disabled={saving}
            className="border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-10 w-full rounded-md border px-3 py-2 text-sm file:border-0 file:bg-transparent file:text-sm file:font-medium focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
          >
            {WEBHOOK_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
          <p className="text-muted-foreground mt-1 text-xs">
            Format the notification payload for your webhook provider.
          </p>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium">Notify on severity</p>
          <label className="flex cursor-pointer items-center gap-3">
            <input
              type="checkbox"
              checked={notifyOnCritical}
              onChange={(e) => setNotifyOnCritical(e.target.checked)}
              disabled={saving}
              className="h-4 w-4 rounded border"
            />
            <span className="text-sm">Critical findings</span>
          </label>
          <label className="flex cursor-pointer items-center gap-3">
            <input
              type="checkbox"
              checked={notifyOnHigh}
              onChange={(e) => setNotifyOnHigh(e.target.checked)}
              disabled={saving}
              className="h-4 w-4 rounded border"
            />
            <span className="text-sm">High findings</span>
          </label>
        </div>
      </div>

      {error && <p className="text-destructive-foreground text-sm">{error}</p>}

      <Button type="submit" disabled={saving}>
        {saving ? "Saving..." : saved ? "Saved" : "Save settings"}
      </Button>
    </form>
  );
}
