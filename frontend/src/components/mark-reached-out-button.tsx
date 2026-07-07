"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { markReachedOut } from "@/lib/api";

export function MarkReachedOutButton({ leadId }: { leadId: string }) {
  const router = useRouter();
  const [pending, setPending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleClick() {
    setPending(true);
    setError(null);
    const result = await markReachedOut(leadId);
    if (result.ok) {
      // Keep the button disabled until the refreshed row replaces it.
      router.refresh();
      return;
    }
    if (result.authExpired) {
      // Send the attorney to sign in again rather than looping on a dead session.
      router.push("/login");
      router.refresh();
      return;
    }
    setPending(false);
    setError(result.error);
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant="outline"
        size="sm"
        onClick={handleClick}
        disabled={pending}
      >
        {pending && <Spinner />}
        Mark as reached out
      </Button>
      {error && (
        <p role="alert" className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
