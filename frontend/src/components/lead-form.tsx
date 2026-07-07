"use client";

import * as React from "react";
import { CheckCircle2, FileUp } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { createLead, type LeadFieldErrors } from "@/lib/api";
import { cn } from "@/lib/utils";

export const MAX_RESUME_BYTES = 5 * 1024 * 1024;
export const RESUME_EXTENSIONS = [".pdf", ".doc", ".docx"];

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface LeadFormValues {
  firstName: string;
  lastName: string;
  email: string;
  resume: File | null;
}

/** Pure client-side validation; returns one message per invalid field. */
export function validateLeadForm(values: LeadFormValues): LeadFieldErrors {
  const errors: LeadFieldErrors = {};
  if (!values.firstName.trim()) {
    errors.first_name = "First name is required.";
  }
  if (!values.lastName.trim()) {
    errors.last_name = "Last name is required.";
  }
  if (!values.email.trim()) {
    errors.email = "Email is required.";
  } else if (!EMAIL_PATTERN.test(values.email.trim())) {
    errors.email = "Enter a valid email address.";
  }
  if (!values.resume || values.resume.name === "") {
    errors.resume = "Please attach your resume.";
  } else {
    const name = values.resume.name.toLowerCase();
    if (!RESUME_EXTENSIONS.some((extension) => name.endsWith(extension))) {
      errors.resume = "Resume must be a PDF, DOC, or DOCX file.";
    } else if (values.resume.size > MAX_RESUME_BYTES) {
      errors.resume = "Resume must be 5 MB or smaller.";
    }
  }
  return errors;
}

type FormStatus = "idle" | "submitting" | "success";

export function LeadForm() {
  const [status, setStatus] = React.useState<FormStatus>("idle");
  const [errors, setErrors] = React.useState<LeadFieldErrors>({});
  const [formError, setFormError] = React.useState<string | null>(null);
  const [fileName, setFileName] = React.useState<string | null>(null);

  function reset() {
    setStatus("idle");
    setErrors({});
    setFormError(null);
    setFileName(null);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    // Read the file off the input element (not FormData) so the original
    // File object — and its true size — is what we validate and upload.
    const resumeInput = form.elements.namedItem("resume");
    const resume =
      resumeInput instanceof HTMLInputElement
        ? (resumeInput.files?.[0] ?? null)
        : null;
    const values: LeadFormValues = {
      firstName: String(data.get("first_name") ?? ""),
      lastName: String(data.get("last_name") ?? ""),
      email: String(data.get("email") ?? ""),
      resume,
    };

    const validationErrors = validateLeadForm(values);
    setErrors(validationErrors);
    setFormError(null);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    const payload = new FormData();
    payload.set("first_name", values.firstName.trim());
    payload.set("last_name", values.lastName.trim());
    payload.set("email", values.email.trim());
    payload.set("resume", values.resume as File);

    setStatus("submitting");
    const result = await createLead(payload);
    if (result.ok) {
      setStatus("success");
      form.reset();
      return;
    }
    setStatus("idle");
    setErrors(result.fieldErrors);
    setFormError(result.formError ?? null);
  }

  if (status === "success") {
    return (
      <div className="flex flex-col items-center gap-4 py-8 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-emerald-500/10">
          <CheckCircle2
            aria-hidden
            className="size-6 text-emerald-600 dark:text-emerald-400"
          />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-lg font-semibold tracking-tight">
            Thank you — we’ve received your information
          </h2>
          <p className="max-w-sm text-sm text-muted-foreground">
            A confirmation email is on its way to you. Our team will review your
            background and reach out about next steps shortly.
          </p>
        </div>
        <Button variant="outline" onClick={reset}>
          Submit another
        </Button>
      </div>
    );
  }

  const submitting = status === "submitting";

  return (
    <form noValidate onSubmit={handleSubmit}>
      <FieldGroup>
        {formError && (
          <Alert variant="destructive">
            <AlertTitle>Submission failed</AlertTitle>
            <AlertDescription>{formError}</AlertDescription>
          </Alert>
        )}

        <div className="grid gap-5 sm:grid-cols-2">
          <Field data-invalid={Boolean(errors.first_name)}>
            <FieldLabel htmlFor="first_name">First name</FieldLabel>
            <Input
              id="first_name"
              name="first_name"
              autoComplete="given-name"
              aria-invalid={Boolean(errors.first_name)}
              aria-describedby={
                errors.first_name ? "first_name-error" : undefined
              }
            />
            <FieldError id="first_name-error">{errors.first_name}</FieldError>
          </Field>

          <Field data-invalid={Boolean(errors.last_name)}>
            <FieldLabel htmlFor="last_name">Last name</FieldLabel>
            <Input
              id="last_name"
              name="last_name"
              autoComplete="family-name"
              aria-invalid={Boolean(errors.last_name)}
              aria-describedby={
                errors.last_name ? "last_name-error" : undefined
              }
            />
            <FieldError id="last_name-error">{errors.last_name}</FieldError>
          </Field>
        </div>

        <Field data-invalid={Boolean(errors.email)}>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            aria-invalid={Boolean(errors.email)}
            aria-describedby={errors.email ? "email-error" : undefined}
          />
          <FieldError id="email-error">{errors.email}</FieldError>
        </Field>

        <Field data-invalid={Boolean(errors.resume)}>
          <FieldLabel htmlFor="resume">Resume</FieldLabel>
          <input
            id="resume"
            name="resume"
            type="file"
            accept=".pdf,.doc,.docx"
            className="peer sr-only"
            aria-invalid={Boolean(errors.resume)}
            aria-describedby={
              errors.resume ? "resume-hint resume-error" : "resume-hint"
            }
            onChange={(event) =>
              setFileName(event.currentTarget.files?.[0]?.name ?? null)
            }
          />
          <label
            htmlFor="resume"
            className={cn(
              "flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-input px-3 py-3 text-sm transition-colors peer-focus-visible:border-ring peer-focus-visible:ring-3 peer-focus-visible:ring-ring/50 hover:bg-muted/50",
              errors.resume && "border-destructive",
            )}
          >
            <FileUp
              aria-hidden
              className="size-4 shrink-0 text-muted-foreground"
            />
            {fileName ? (
              <span className="truncate font-medium">{fileName}</span>
            ) : (
              <span className="text-muted-foreground">
                Choose a file or drop it here
              </span>
            )}
          </label>
          <FieldDescription id="resume-hint">
            PDF, DOC, or DOCX · max 5 MB
          </FieldDescription>
          <FieldError id="resume-error">{errors.resume}</FieldError>
        </Field>

        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={submitting}
        >
          {submitting ? (
            <>
              <Spinner /> Submitting…
            </>
          ) : (
            "Submit information"
          )}
        </Button>
      </FieldGroup>
    </form>
  );
}
