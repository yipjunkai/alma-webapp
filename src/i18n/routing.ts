import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  // All locales that are supported. `en-US` is the default.
  locales: ["en-US", "es-ES"],
  defaultLocale: "en-US",
});

export type Locale = (typeof routing.locales)[number];
