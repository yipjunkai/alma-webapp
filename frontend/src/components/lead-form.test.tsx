import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LeadForm, MAX_RESUME_BYTES } from "./lead-form";

function makeFile(name: string, size = 1024): File {
  const file = new File(["resume"], name, { type: "application/pdf" });
  Object.defineProperty(file, "size", { value: size });
  return file;
}

async function fillValidFields(user = userEvent.setup()) {
  await user.type(screen.getByLabelText("First name"), "Jane");
  await user.type(screen.getByLabelText("Last name"), "Doe");
  await user.type(screen.getByLabelText("Email"), "jane@example.com");
  await user.upload(screen.getByLabelText("Resume"), makeFile("resume.pdf"));
  return user;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("LeadForm validation", () => {
  it("shows an error for every field on empty submit and does not call fetch", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<LeadForm />);

    await userEvent.click(
      screen.getByRole("button", { name: "Submit information" }),
    );

    expect(
      await screen.findByText("First name is required."),
    ).toBeInTheDocument();
    expect(screen.getByText("Last name is required.")).toBeInTheDocument();
    expect(screen.getByText("Email is required.")).toBeInTheDocument();
    expect(screen.getByText("Please attach your resume.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects a malformed email", async () => {
    render(<LeadForm />);
    const user = await fillValidFields();
    await user.clear(screen.getByLabelText("Email"));
    await user.type(screen.getByLabelText("Email"), "not-an-email");

    await user.click(
      screen.getByRole("button", { name: "Submit information" }),
    );

    expect(
      await screen.findByText("Enter a valid email address."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });

  it("rejects a resume over 5 MB", async () => {
    render(<LeadForm />);
    const user = await fillValidFields();
    await user.upload(
      screen.getByLabelText("Resume"),
      makeFile("resume.pdf", MAX_RESUME_BYTES + 1),
    );

    await user.click(
      screen.getByRole("button", { name: "Submit information" }),
    );

    expect(
      await screen.findByText("Resume must be 5 MB or smaller."),
    ).toBeInTheDocument();
  });

  it("rejects a disallowed file extension", async () => {
    render(<LeadForm />);
    // `applyAccept: false` lets the test hand the input a file the browser
    // picker would normally filter out, exercising our own extension check.
    const user = await fillValidFields(userEvent.setup({ applyAccept: false }));
    await user.upload(screen.getByLabelText("Resume"), makeFile("resume.exe"));

    await user.click(
      screen.getByRole("button", { name: "Submit information" }),
    );

    expect(
      await screen.findByText("Resume must be a PDF, DOC, or DOCX file."),
    ).toBeInTheDocument();
  });
});

describe("LeadForm submission", () => {
  it("posts multipart form data and shows the success state on 201", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      status: 201,
      ok: true,
      json: async () => ({ id: "1", state: "PENDING" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<LeadForm />);
    const user = await fillValidFields();

    await user.click(
      screen.getByRole("button", { name: "Submit information" }),
    );

    expect(
      await screen.findByText(/thank you — we’ve received your information/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Submit another" }),
    ).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/leads");
    expect(init.method).toBe("POST");
    const body = init.body as FormData;
    expect(body.get("first_name")).toBe("Jane");
    expect(body.get("last_name")).toBe("Doe");
    expect(body.get("email")).toBe("jane@example.com");
    expect((body.get("resume") as File).name).toBe("resume.pdf");
  });

  it("maps a 422 response back onto the offending field", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      status: 422,
      ok: false,
      json: async () => ({
        detail: [
          { loc: ["body", "email"], msg: "value is not a valid email address" },
        ],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<LeadForm />);
    const user = await fillValidFields();

    await user.click(
      screen.getByRole("button", { name: "Submit information" }),
    );

    expect(
      await screen.findByText("value is not a valid email address"),
    ).toBeInTheDocument();
  });

  it("shows a general error alert on network failure", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("failed"));
    vi.stubGlobal("fetch", fetchMock);
    render(<LeadForm />);
    const user = await fillValidFields();

    await user.click(
      screen.getByRole("button", { name: "Submit information" }),
    );

    expect(
      await screen.findByText("Something went wrong. Please try again."),
    ).toBeInTheDocument();
  });
});
