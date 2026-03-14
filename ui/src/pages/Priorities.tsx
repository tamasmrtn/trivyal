import {
  FixTodaySection,
  UpdateWhenYouCanSection,
} from "@/features/priorities";

export function Priorities() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold">Priorities</h1>
        <p className="text-muted-foreground text-sm">
          What to act on across your infrastructure
        </p>
      </div>

      <FixTodaySection />

      <div className="border-t" />

      <UpdateWhenYouCanSection />
    </div>
  );
}
