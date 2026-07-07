import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { login } from "@/lib/api";
import { LoginForm } from "./login-form";

const { push, refresh } = vi.hoisted(() => ({
  push: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

vi.mock("@/lib/api", () => ({ login: vi.fn() }));

const mockLogin = vi.mocked(login);

beforeEach(() => {
  vi.clearAllMocks();
});

async function signIn() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Email"), "attorney@example.com");
  await user.type(screen.getByLabelText("Password"), "changeme");
  await user.click(screen.getByRole("button", { name: /sign in/i }));
}

describe("LoginForm", () => {
  it("navigates to the queue on success", async () => {
    mockLogin.mockResolvedValue({ ok: true });
    render(<LoginForm />);

    await signIn();

    expect(mockLogin).toHaveBeenCalledWith("attorney@example.com", "changeme");
    expect(push).toHaveBeenCalledWith("/admin/leads");
  });

  it("shows an error and stays put on invalid credentials", async () => {
    mockLogin.mockResolvedValue({
      ok: false,
      error: "Invalid email or password.",
    });
    render(<LoginForm />);

    await signIn();

    expect(
      await screen.findByText("Invalid email or password."),
    ).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });
});
