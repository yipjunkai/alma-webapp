import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { logout } from "@/lib/api";
import { LogoutButton } from "./logout-button";

const { push, refresh } = vi.hoisted(() => ({
  push: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

vi.mock("@/lib/api", () => ({ logout: vi.fn() }));

const mockLogout = vi.mocked(logout);

beforeEach(() => {
  vi.clearAllMocks();
});

async function click() {
  await userEvent.click(screen.getByRole("button", { name: /log out/i }));
}

describe("LogoutButton", () => {
  it("returns to /login on success", async () => {
    mockLogout.mockResolvedValue({ ok: true });
    render(<LogoutButton />);

    await click();

    expect(push).toHaveBeenCalledWith("/login");
  });

  it("surfaces an error and stays put when logout fails", async () => {
    mockLogout.mockResolvedValue({ ok: false });
    render(<LogoutButton />);

    await click();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /could not sign out/i,
    );
    expect(push).not.toHaveBeenCalled();
  });
});
