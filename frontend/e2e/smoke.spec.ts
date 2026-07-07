import { expect, test } from "@playwright/test";

// Happy-path smoke: the app boots and the public lead form renders.
test("home page renders the lead intake landing", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Get an assessment of your immigration case",
  );
  await expect(page.getByLabel("First name")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Submit information" }),
  ).toBeVisible();
});
