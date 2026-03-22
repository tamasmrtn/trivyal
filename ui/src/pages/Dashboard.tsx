import React from "react";
import { useNavigate } from "react-router-dom";
import {
  PatchSummaryCard,
  SummaryCards,
  useDashboard,
} from "@/features/dashboard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Wrench, ArrowUpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useFixable } from "@/lib/hooks/useFixable";
import { fetchPatchSummary } from "@/lib/api/patches";
import type { PatchSummary } from "@/lib/api/types";
import { useEffect, useState } from "react";

export function Dashboard() {
  const [fixable, toggleFixable] = useFixable();
  const { data, loading, error } = useDashboard(fixable || undefined);
  const navigate = useNavigate();
  const [patchSummary, setPatchSummary] = useState<PatchSummary | null>(null);

  useEffect(() => {
    fetchPatchSummary()
      .then(setPatchSummary)
      .catch(() => {});
  }, []);

  if (loading) {
    return (
      <div>
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-8 w-28" />
        </div>
        <div className="space-y-8">
          <section>
            <Skeleton className="mb-4 h-6 w-36" />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="rounded-lg border p-6">
                  <Skeleton className="mb-4 h-4 w-20" />
                  <Skeleton className="h-8 w-12" />
                </div>
              ))}
            </div>
          </section>
          <section>
            <Skeleton className="mb-4 h-6 w-24" />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rounded-lg border p-6">
                  <Skeleton className="mb-4 h-4 w-20" />
                  <Skeleton className="h-8 w-12" />
                </div>
              ))}
            </div>
          </section>
        </div>
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

  if (!data) return null;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={toggleFixable}
          className={cn(fixable && "bg-primary text-primary-foreground")}
        >
          Fixable only
        </Button>
      </div>

      <SummaryCards data={data} />

      <div className="mt-8 border-t pt-8">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card
            role="link"
            tabIndex={0}
            className="hover:border-primary/50 cursor-pointer transition-colors"
            onClick={() => navigate("/priorities")}
            onKeyDown={(e: React.KeyboardEvent) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                navigate("/priorities");
              }
            }}
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Fix Today</CardTitle>
              <Wrench className="text-primary h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {data.misconfig.total_active}
              </div>
              <p className="text-muted-foreground text-sm">
                configuration issues
              </p>
            </CardContent>
          </Card>
          <Card
            role="link"
            tabIndex={0}
            className="hover:border-primary/50 cursor-pointer transition-colors"
            onClick={() => navigate("/priorities")}
            onKeyDown={(e: React.KeyboardEvent) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                navigate("/priorities");
              }
            }}
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Fixable CVEs
              </CardTitle>
              <ArrowUpCircle className="text-primary h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.fixable_cves}</div>
              <p className="text-muted-foreground text-sm">
                with upstream fixes available
              </p>
            </CardContent>
          </Card>
          {patchSummary?.patching_available && (
            <PatchSummaryCard
              totalPatched={patchSummary.total_patched}
              findingsResolved={patchSummary.findings_resolved}
            />
          )}
        </div>
      </div>
    </div>
  );
}
