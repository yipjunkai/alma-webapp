import { getTranslations, setRequestLocale } from "next-intl/server";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LocaleSwitcher } from "@/components/locale-switcher";
import type { Locale } from "@/i18n/routing";

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function HomePage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale as Locale);

  const t = await getTranslations("HomePage");

  const features = [
    { title: t("stack.nextjs.title"), body: t("stack.nextjs.body") },
    { title: t("stack.tailwind.title"), body: t("stack.tailwind.body") },
    { title: t("stack.shadcn.title"), body: t("stack.shadcn.body") },
    { title: t("stack.intl.title"), body: t("stack.intl.body") },
  ];

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between px-6 py-4">
        <span className="text-sm font-semibold tracking-tight">Alma</span>
        <LocaleSwitcher />
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center gap-10 px-6 py-16 text-center">
        <div className="flex flex-col items-center gap-5">
          <span className="inline-flex items-center rounded-full border border-border bg-muted/40 px-3 py-1 text-xs font-medium text-muted-foreground">
            {t("badge")}
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            {t("title")}
          </h1>
          <p className="max-w-2xl text-base text-pretty text-muted-foreground sm:text-lg">
            {t("subtitle")}
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button size="lg">{t("primaryCta")}</Button>
          <Button size="lg" variant="outline">
            {t("secondaryCta")}
          </Button>
        </div>

        <section className="w-full">
          <h2 className="mb-4 text-sm font-medium text-muted-foreground">
            {t("stack.title")}
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {features.map((feature) => (
              <Card key={feature.title} className="text-left">
                <CardHeader>
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.body}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>
      </main>

      <footer className="px-6 py-6 text-center text-xs text-muted-foreground">
        {t("footer", { locale })}
      </footer>
    </div>
  );
}
