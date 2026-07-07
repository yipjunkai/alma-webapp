import { NextResponse, type NextRequest } from "next/server";

// Kept standalone (no shared imports) per the proxy docs guidance.
const SESSION_COOKIE = "alma_session";

// UX-only guard: bounce cookie-less visitors off /admin/* before render.
// The backend is the real enforcement — the admin page redirects on 401
// when the cookie exists but is invalid/expired.
export function proxy(request: NextRequest) {
  if (!request.cookies.get(SESSION_COOKIE)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: "/admin/:path*",
};
