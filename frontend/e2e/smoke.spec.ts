import { expect, test } from "@playwright/test";

// Happy-path smoke: the app boots and the landing renders.
test("home page renders the Alma landing", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Alma");
});
