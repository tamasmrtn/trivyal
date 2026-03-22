import React from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Wrench } from "lucide-react";

interface PatchSummaryCardProps {
  totalPatched: number;
  findingsResolved: number;
}

export function PatchSummaryCard({
  totalPatched,
  findingsResolved,
}: PatchSummaryCardProps) {
  const navigate = useNavigate();

  return (
    <Card
      role="link"
      tabIndex={0}
      className="hover:border-primary/50 cursor-pointer transition-colors"
      onClick={() => navigate("/patches")}
      onKeyDown={(e: React.KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          navigate("/patches");
        }
      }}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">Patches</CardTitle>
        <Wrench className="text-primary h-4 w-4" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{totalPatched}</div>
        <p className="text-muted-foreground text-sm">
          {findingsResolved} finding{findingsResolved !== 1 ? "s" : ""} resolved
        </p>
      </CardContent>
    </Card>
  );
}
