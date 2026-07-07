import { Spinner } from "@/components/ui/spinner";

export default function Loading() {
  return (
    <div className="flex min-h-svh items-center justify-center gap-2 text-muted-foreground">
      <Spinner className="size-5" />
      <span className="text-sm">Loading leads…</span>
    </div>
  );
}
