import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-5 px-6 text-center">
      <p className="text-sm font-medium text-muted-foreground">404</p>
      <div className="space-y-1.5">
        <h1 className="text-xl font-semibold tracking-tight">Page not found</h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          The page you&rsquo;re looking for doesn&rsquo;t exist or has moved.
        </p>
      </div>
      <Link href="/" className={cn(buttonVariants())}>
        Back to the form
      </Link>
    </main>
  );
}
