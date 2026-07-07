import type { Metadata } from "next";
import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Check, FileText, Inbox } from "lucide-react";

import { LogoutButton } from "@/components/logout-button";
import { MarkReachedOutButton } from "@/components/mark-reached-out-button";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  fetchLeads,
  SESSION_COOKIE,
  type LeadListResponse,
  type LeadState,
} from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Leads — Alma",
};

function StateBadge({ state }: { state: LeadState }) {
  if (state === "PENDING") {
    return (
      <Badge
        variant="secondary"
        className="bg-amber-500/15 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400"
      >
        Pending
      </Badge>
    );
  }
  return (
    <Badge
      variant="secondary"
      className="bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400"
    >
      Reached out
    </Badge>
  );
}

const PAGE_SIZE = 20;

export default async function AdminLeadsPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string; page?: string }>;
}) {
  const { state, page: pageParam } = await searchParams;
  const stateFilter: LeadState | undefined =
    state === "PENDING" || state === "REACHED_OUT" ? state : undefined;
  const page = Math.max(1, Number(pageParam) || 1);

  const cookieStore = await cookies();
  const session = cookieStore.get(SESSION_COOKIE);
  if (!session) {
    redirect("/login");
  }

  const response = await fetchLeads(
    `${SESSION_COOKIE}=${session.value}`,
    stateFilter,
    PAGE_SIZE,
    (page - 1) * PAGE_SIZE,
  );
  if (response.status === 401) {
    redirect("/login");
  }
  if (!response.ok) {
    throw new Error(`Failed to load leads (${response.status})`);
  }
  const { items, total } = (await response.json()) as LeadListResponse;

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageHref = (p: number) => {
    const params = new URLSearchParams();
    if (stateFilter) params.set("state", stateFilter);
    if (p > 1) params.set("page", String(p));
    const qs = params.toString();
    return qs ? `/admin/leads?${qs}` : "/admin/leads";
  };

  const tabs = [
    { label: "All", href: "/admin/leads", active: !stateFilter },
    {
      label: "Pending",
      href: "/admin/leads?state=PENDING",
      active: stateFilter === "PENDING",
    },
    {
      label: "Reached out",
      href: "/admin/leads?state=REACHED_OUT",
      active: stateFilter === "REACHED_OUT",
    },
  ];

  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-3.5">
          <div className="flex items-baseline gap-2.5">
            <span className="font-semibold tracking-tight">Alma</span>
            <span className="text-sm text-muted-foreground">
              Attorney portal
            </span>
          </div>
          <LogoutButton />
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Leads</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {total} {total === 1 ? "lead" : "leads"} · newest first
            </p>
          </div>

          <nav
            aria-label="Filter leads by state"
            className="inline-flex items-center gap-0.5 rounded-lg bg-muted p-0.5"
          >
            {tabs.map((tab) => (
              <Link
                key={tab.label}
                href={tab.href}
                aria-current={tab.active ? "page" : undefined}
                className={cn(
                  "rounded-md px-3 py-1 text-sm font-medium transition-colors",
                  tab.active
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {tab.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="mt-6 overflow-x-auto rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Resume</TableHead>
                <TableHead>State</TableHead>
                <TableHead>Submitted</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6}>
                    <div className="flex flex-col items-center gap-2 py-12 text-center">
                      <Inbox
                        aria-hidden
                        className="size-6 text-muted-foreground"
                      />
                      <p className="font-medium">
                        {stateFilter === "PENDING"
                          ? "No pending leads"
                          : stateFilter === "REACHED_OUT"
                            ? "No leads have been reached out to yet"
                            : "No leads yet"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        New submissions from the public form will appear here.
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                items.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell className="font-medium">
                      {lead.first_name} {lead.last_name}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {lead.email}
                    </TableCell>
                    <TableCell>
                      <a
                        href={`/api/leads/${lead.id}/resume`}
                        className="inline-flex max-w-48 items-center gap-1.5 underline-offset-4 hover:underline"
                      >
                        <FileText
                          aria-hidden
                          className="size-3.5 shrink-0 text-muted-foreground"
                        />
                        <span className="truncate">{lead.resume_filename}</span>
                      </a>
                    </TableCell>
                    <TableCell>
                      <StateBadge state={lead.state} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(lead.created_at, "UTC")} UTC
                    </TableCell>
                    <TableCell className="text-right">
                      {lead.state === "PENDING" ? (
                        <MarkReachedOutButton leadId={lead.id} />
                      ) : (
                        <span className="inline-flex items-center gap-1 text-muted-foreground">
                          <Check aria-hidden className="size-3.5" />
                          <span className="sr-only">Reached out</span>—
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {totalPages > 1 && (
          <nav
            aria-label="Pagination"
            className="mt-4 flex items-center justify-between"
          >
            <p className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              {page > 1 ? (
                <Link
                  href={pageHref(page - 1)}
                  className={cn(
                    buttonVariants({ variant: "outline", size: "sm" }),
                  )}
                >
                  Previous
                </Link>
              ) : (
                <span
                  aria-disabled
                  className={cn(
                    buttonVariants({ variant: "outline", size: "sm" }),
                    "pointer-events-none opacity-50",
                  )}
                >
                  Previous
                </span>
              )}
              {page < totalPages ? (
                <Link
                  href={pageHref(page + 1)}
                  className={cn(
                    buttonVariants({ variant: "outline", size: "sm" }),
                  )}
                >
                  Next
                </Link>
              ) : (
                <span
                  aria-disabled
                  className={cn(
                    buttonVariants({ variant: "outline", size: "sm" }),
                    "pointer-events-none opacity-50",
                  )}
                >
                  Next
                </span>
              )}
            </div>
          </nav>
        )}
      </main>
    </div>
  );
}
