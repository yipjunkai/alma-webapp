import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Lightweight wrappers around Next.js' navigation APIs that
// automatically consider the routing configuration (locale prefixes).
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
