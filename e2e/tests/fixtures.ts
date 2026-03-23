import { test as base, expect } from "@playwright/test";

const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "testpassword";

/**
 * Extends the base test with an `authedPage` fixture that logs in
 * via the UI form before each test.
 */
export const test = base.extend<{ authedPage: ReturnType<typeof base.extend> }>({
  authedPage: async ({ page }, use) => {
    await page.goto("/login");
    await page.locator("#username").fill("admin");
    await page.locator("#password").fill(ADMIN_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
    await use(page);
  },
});

export { expect };
