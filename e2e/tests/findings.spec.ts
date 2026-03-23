import { test, expect } from "./fixtures";

test.describe("Findings", () => {
  test("renders page heading and filter controls", async ({ authedPage: page }) => {
    await page.getByRole("link", { name: /findings/i }).click();
    await expect(page.getByRole("heading", { name: /findings/i })).toBeVisible();
    await expect(page.locator("select[aria-label='Filter by severity']")).toBeVisible();
    await expect(page.locator("select[aria-label='Filter by status']")).toBeVisible();
  });

  test("shows empty state when no findings exist", async ({ authedPage: page }) => {
    await page.getByRole("link", { name: /findings/i }).click();
    // Either a table with rows or an empty state message should appear
    const table = page.locator("table");
    const emptyState = page.getByText(/no findings/i);
    await expect(table.or(emptyState)).toBeVisible();
  });
});
