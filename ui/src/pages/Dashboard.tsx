import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { SummaryCards, useDashboard } from "@/features/dashboard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Wrench, ArrowUpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function Dashboard() {
  const [fixable, setFixable] = useState(false);
  const { data, loading, error } = useDashboard(fixable || undefined);
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading dashboard...</p>
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
          onClick={() => setFixable(!fixable)}
          className={cn(fixable && "bg-primary text-primary-foreground")}
        >
          Fixable only
        </Button>
      </div>

      <SummaryCards data={data} />

      <div className="mt-8 border-t pt-8">
        <div className="grid gap-4 sm:grid-cols-2">
          <Card
            className="hover:border-primary/50 cursor-pointer transition-colors"
            onClick={() => navigate("/priorities")}
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
            className="hover:border-primary/50 cursor-pointer transition-colors"
            onClick={() => navigate("/priorities")}
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
        </div>
      </div>
    </div>
  );
}
