import { NotificationSettingsForm, useSettings } from "@/features/settings";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function Settings() {
  const { data, loading, error, refetch } = useSettings();

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading settings...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-destructive-foreground">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
      </div>
      <div className="max-w-lg">
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Configure webhook alerts for new critical and high severity
              findings.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {data && (
              <NotificationSettingsForm initial={data} onSaved={refetch} />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
