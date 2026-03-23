import { test, expect } from "./fixtures";

test.describe("Agents", () => {
  test("renders page heading and add button", async ({ authedPage: page }) => {
    await page.getByRole("link", { name: /agents/i }).click();
    await expect(page.getByRole("heading", { name: /agents/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /add agent/i })).toBeVisible();
  });

  test("opens add agent dialog", async ({ authedPage: page }) => {
    await page.getByRole("link", { name: /agents/i }).click();
    await page.getByRole("button", { name: /add agent/i }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.locator("#agent-name")).toBeVisible();
    await expect(page.getByRole("button", { name: /register/i })).toBeVisible();
  });

  test("registers a new agent", async ({ authedPage: page }) => {
    await page.getByRole("link", { name: /agents/i }).click();
    await page.getByRole("button", { name: /add agent/i }).click();
    await page.locator("#agent-name").fill("e2e-test-agent");
    await page.getByRole("button", { name: /register/i }).click();

    // After registration, dialog shows token and compose snippet
    await expect(page.getByText(/agent registered/i)).toBeVisible();
    await expect(page.getByText(/token/i)).toBeVisible();
  });
});
