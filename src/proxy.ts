import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

// Next.js 16 renamed `middleware` to `proxy`. `next-intl` still ships the
// handler from `next-intl/middleware`; it just lives in `proxy.ts` now.
export default createMiddleware(routing);

export const config = {
  // Match all pathnames except for
  // - … those starting with `/api`, `/trpc`, `/_next` or `/_vercel`
  // - … the ones containing a dot (e.g. `favicon.ico`)
  matcher: "/((?!api|trpc|_next|_vercel|.*\\..*).*)",
};
