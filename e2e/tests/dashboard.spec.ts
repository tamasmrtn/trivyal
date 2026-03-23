import { test, expect } from "./fixtures";

test.describe("Dashboard", () => {
  test("renders page heading and summary sections", async ({ authedPage: page }) => {
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /vulnerabilities/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /agents/i })).toBeVisible();
  });

  test("renders severity cards", async ({ authedPage: page }) => {
    for (const severity of ["Critical", "High", "Medium", "Low", "Unknown"]) {
      await expect(page.getByText(severity).first()).toBeVisible();
    }
  });

  test("fixable only toggle is present", async ({ authedPage: page }) => {
    await expect(page.getByRole("button", { name: /fixable only/i })).toBeVisible();
  });
});
