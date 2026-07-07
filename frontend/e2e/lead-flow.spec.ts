import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const RESUME_FIXTURE = path.join(__dirname, "fixtures", "resume.pdf");

const ATTORNEY_EMAIL = "attorney@example.com";
const ATTORNEY_PASSWORD = "changeme";

/** The queue row for a given lead, matched by its unique email. */
function leadRow(page: Page, email: string) {
  return page.getByRole("row").filter({ hasText: email });
}

test("visiting the admin queue while logged out lands on the login page", async ({
  page,
}) => {
  await page.goto("/admin/leads");
  await expect(page).toHaveURL("/login");
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("a public submission flows through the attorney queue to reached out", async ({
  page,
}) => {
  // Unique prospect per run so re-runs never collide on an existing row.
  const runId = Date.now();
  const prospectEmail = `prospect.${runId}@example.com`;

  // 1. Prospect submits the public lead form.
  await page.goto("/");
  await page.getByLabel("First name").fill("Casey");
  await page.getByLabel("Last name").fill(`Prospect ${runId}`);
  await page.getByLabel("Email").fill(prospectEmail);
  await page.getByLabel("Resume").setInputFiles(RESUME_FIXTURE);
  await page.getByRole("button", { name: "Submit information" }).click();
  await expect(
    page.getByRole("heading", { name: /received your information/i }),
  ).toBeVisible();

  // 2. Attorney signs in.
  await page.goto("/login");
  await page.getByLabel("Email").fill(ATTORNEY_EMAIL);
  await page.getByLabel("Password").fill(ATTORNEY_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL("/admin/leads");
  await expect(page.getByRole("heading", { name: "Leads" })).toBeVisible();

  // 3. The new lead shows up as PENDING with a downloadable resume.
  const row = leadRow(page, prospectEmail);
  await expect(row).toBeVisible();
  await expect(
    row.getByRole("cell", { name: "Pending", exact: true }),
  ).toBeVisible();
  const resumeLink = row.getByRole("link", { name: "resume.pdf" });
  await expect(resumeLink).toHaveAttribute("href", /\/api\/leads\/.+\/resume$/);

  // 4. Mark the lead as reached out; the badge flips in place.
  await row.getByRole("button", { name: "Mark as reached out" }).click();
  await expect(
    row.getByRole("cell", { name: "Reached out", exact: true }),
  ).toBeVisible();
  await expect(
    row.getByRole("cell", { name: "Pending", exact: true }),
  ).toBeHidden();

  // 5. The transition is persisted, not just optimistic UI.
  await page.reload();
  await expect(row).toBeVisible();
  await expect(
    row.getByRole("cell", { name: "Reached out", exact: true }),
  ).toBeVisible();
  await expect(
    row.getByRole("button", { name: "Mark as reached out" }),
  ).toBeHidden();
});
