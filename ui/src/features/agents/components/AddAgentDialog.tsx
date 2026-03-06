import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createAgent } from "@/lib/api/agents";
import type { AgentRegistered } from "@/lib/api/types";
import { Check, Copy, Plus } from "lucide-react";

interface AddAgentDialogProps {
  onCreated: () => void;
}

function buildDockerCompose(token: string, hubPublicKey: string): string {
  return `name: trivyal-agent
services:
  trivyal-agent:
    image: ghcr.io/tamasmrtn/trivyal-agent:latest
    restart: unless-stopped
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data:/app/data
    environment:
      TRIVYAL_HUB_URL: "ws://<HUB_HOST>:8099"
      TRIVYAL_TOKEN: "${token}"
      TRIVYAL_KEY: "${hubPublicKey}"
      TRIVYAL_SCAN_SCHEDULE: "0 2 * * *"
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:8100/health || exit 1"]
      interval: 60s
      timeout: 5s
      retries: 3
      start_period: 15s`;
}

export function AddAgentDialog({ onCreated }: AddAgentDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentRegistered | null>(null);
  const [copied, setCopied] = useState(false);

  function reset() {
    setName("");
    setSubmitting(false);
    setError(null);
    setResult(null);
    setCopied(false);
  }

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (!next) {
      if (result) onCreated();
      reset();
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const registered = await createAgent(name.trim());
      setResult(registered);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add agent");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCopy() {
    if (!result) return;
    const snippet = buildDockerCompose(result.token, result.hub_public_key);
    await navigator.clipboard.writeText(snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          Add Agent
        </Button>
      </DialogTrigger>
      <DialogContent>
        {!result ? (
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Add Agent</DialogTitle>
              <DialogDescription>
                Register a new agent to start scanning containers on a host.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <label
                htmlFor="agent-name"
                className="mb-2 block text-sm font-medium"
              >
                Agent name
              </label>
              <Input
                id="agent-name"
                placeholder="e.g. server-1"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={submitting}
                autoFocus
              />
              {error && (
                <p className="text-destructive-foreground mt-2 text-sm">
                  {error}
                </p>
              )}
            </div>
            <DialogFooter>
              <Button type="submit" disabled={submitting || !name.trim()}>
                {submitting ? "Registering..." : "Register"}
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Agent Registered</DialogTitle>
              <DialogDescription>
                Deploy the agent using the Docker Compose snippet below. The
                token is shown only once.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <p className="mb-1 text-sm font-medium">Token</p>
                <code className="bg-muted block rounded px-3 py-2 text-sm break-all">
                  {result.token}
                </code>
              </div>
              <div>
                <p className="mb-1 text-sm font-medium">Hub Public Key</p>
                <code className="bg-muted block rounded px-3 py-2 text-sm break-all">
                  {result.hub_public_key}
                </code>
              </div>
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <p className="text-sm font-medium">Docker Compose</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopy}
                    aria-label="Copy docker compose snippet"
                  >
                    {copied ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                    {copied ? "Copied" : "Copy"}
                  </Button>
                </div>
                <pre className="bg-muted overflow-x-auto rounded p-3 text-xs">
                  {buildDockerCompose(result.token, result.hub_public_key)}
                </pre>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
