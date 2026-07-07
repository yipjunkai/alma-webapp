import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { LoginForm } from "@/components/login-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchMe, SESSION_COOKIE } from "@/lib/api";

export const metadata: Metadata = {
  title: "Sign in — Alma",
};

export default async function LoginPage() {
  const cookieStore = await cookies();
  const session = cookieStore.get(SESSION_COOKIE);

  let authenticated = false;
  if (session) {
    try {
      const response = await fetchMe(`${SESSION_COOKIE}=${session.value}`);
      authenticated = response.ok;
    } catch {
      // Backend unreachable — treat as signed out and render the form rather
      // than crashing to the framework error page.
    }
  }
  // `redirect()` throws internally, so it must run outside the try/catch above.
  if (authenticated) {
    redirect("/admin/leads");
  }

  return (
    <main className="flex min-h-svh items-center justify-center bg-muted/40 p-6">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <p className="text-lg font-semibold tracking-tight">Alma</p>
          <p className="text-sm text-muted-foreground">Attorney portal</p>
        </div>
        <Card className="[--card-spacing:--spacing(6)]">
          <CardHeader>
            <CardTitle>Sign in</CardTitle>
            <CardDescription>
              Use your attorney account to view the lead queue.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LoginForm />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
