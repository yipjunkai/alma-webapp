import { ScrollText, ShieldCheck } from "lucide-react";

import { LeadForm } from "@/components/lead-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="grid min-h-svh lg:grid-cols-[1.1fr_1fr]">
      <section className="relative flex flex-col justify-between gap-10 bg-primary p-8 text-primary-foreground sm:p-12">
        <ScrollText
          aria-hidden
          className="pointer-events-none absolute right-8 bottom-8 hidden size-40 text-primary-foreground/5 lg:block"
        />

        <p className="text-lg font-semibold tracking-tight">Alma</p>

        <div className="max-w-md">
          <h1 className="text-4xl/tight font-semibold tracking-tight text-balance sm:text-5xl/tight">
            Get an assessment of your immigration case
          </h1>
          <p className="mt-5 text-base/relaxed text-pretty text-primary-foreground/70">
            Tell us a little about yourself and share your resume — our
            attorneys will review your background and follow up with a
            personalized path forward.
          </p>
        </div>

        <p className="flex items-center gap-2 text-sm text-primary-foreground/60">
          <ShieldCheck aria-hidden className="size-4 shrink-0" />
          Confidential — your information is only used to assess your case.
        </p>
      </section>

      <main className="flex items-center justify-center p-6 py-12 sm:p-12">
        <Card className="w-full max-w-md [--card-spacing:--spacing(6)]">
          <CardHeader>
            <CardTitle className="text-xl">Start your assessment</CardTitle>
            <CardDescription>
              A few details are all we need to get started.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LeadForm />
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
