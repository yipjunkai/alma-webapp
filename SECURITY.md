# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** — do not open a public issue.

Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability):
open the repository's **Security** tab and choose **Report a vulnerability**.

Please include steps to reproduce, the affected component, and any relevant logs
or proof of concept. Reports are typically acknowledged within a few business days.

## Scope

This is a demonstration application. The security posture — what is validated and
enforced, plus deliberate scope cuts (rate limiting, CAPTCHA, virus scanning, TLS,
audit logging) — is documented in [docs/DESIGN.md](docs/DESIGN.md#security-posture-and-known-cuts).

## Supported versions

Only the latest commit on the `main` branch is maintained.
