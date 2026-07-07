"use client";

import { useLocale, useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LocaleSwitcher() {
  const t = useTranslations("LocaleSwitcher");
  const activeLocale = useLocale();
  // Pathname without the locale prefix, so switching keeps the same page.
  const pathname = usePathname();

  return (
    <nav aria-label={t("label")} className="flex items-center gap-1">
      {routing.locales.map((locale) => {
        const isActive = locale === activeLocale;
        return (
          <Link
            key={locale}
            href={pathname}
            locale={locale}
            aria-current={isActive ? "true" : undefined}
            className={cn(
              buttonVariants({
                variant: isActive ? "default" : "ghost",
                size: "sm",
              }),
            )}
          >
            {t(locale)}
          </Link>
        );
      })}
    </nav>
  );
}
