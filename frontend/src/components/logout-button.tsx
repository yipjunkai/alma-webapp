"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { logout } from "@/lib/api";

export function LogoutButton() {
  const router = useRouter();
  const [pending, setPending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleClick() {
    setPending(true);
    setError(null);
    const result = await logout();
    if (!result.ok) {
      // The httpOnly cookie can only be cleared server-side; if that failed,
      // navigating to /login would just bounce back. Let them retry instead.
      setPending(false);
      setError("Could not sign out. Please try again.");
      return;
    }
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant="outline"
        size="sm"
        onClick={handleClick}
        disabled={pending}
      >
        {pending ? <Spinner /> : <LogOut aria-hidden />}
        Log out
      </Button>
      {error && (
        <p role="alert" className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
