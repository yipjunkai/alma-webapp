import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { markReachedOut } from "@/lib/api";
import { MarkReachedOutButton } from "./mark-reached-out-button";

const { push, refresh } = vi.hoisted(() => ({
  push: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

vi.mock("@/lib/api", () => ({ markReachedOut: vi.fn() }));

const mockMark = vi.mocked(markReachedOut);

beforeEach(() => {
  vi.clearAllMocks();
});

async function click() {
  await userEvent.click(
    screen.getByRole("button", { name: /mark as reached out/i }),
  );
}

describe("MarkReachedOutButton", () => {
  it("refreshes the queue after a successful transition", async () => {
    mockMark.mockResolvedValue({ ok: true });
    render(<MarkReachedOutButton leadId="lead-1" />);

    await click();

    expect(mockMark).toHaveBeenCalledWith("lead-1");
    expect(refresh).toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });

  it("routes to /login when the session has expired", async () => {
    mockMark.mockResolvedValue({
      ok: false,
      authExpired: true,
      error: "Your session expired — please sign in again.",
    });
    render(<MarkReachedOutButton leadId="lead-1" />);

    await click();

    expect(push).toHaveBeenCalledWith("/login");
  });

  it("shows an inline error on conflict without navigating", async () => {
    mockMark.mockResolvedValue({
      ok: false,
      error: "Lead was already updated — refresh to see the latest.",
    });
    render(<MarkReachedOutButton leadId="lead-1" />);

    await click();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /already updated/i,
    );
    expect(push).not.toHaveBeenCalled();
  });
});
