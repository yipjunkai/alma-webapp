import { routing } from "@/i18n/routing";
import messages from "@/i18n/messages/en-US.json";

// Global type augmentation for next-intl: gives `useTranslations`, `Link`,
// locales, etc. full type safety based on the default (`en-US`) messages.
declare module "next-intl" {
  interface AppConfig {
    Locale: (typeof routing.locales)[number];
    Messages: typeof messages;
  }
}
