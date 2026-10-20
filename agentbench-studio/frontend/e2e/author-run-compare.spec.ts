import { test, expect } from "@playwright/test";

// Requires the stack: `docker compose up -d` (uses offline mock:* models, no API keys needed).
test("author a task, run two models, see them compared", async ({ page }) => {
  const name = `Capital city ${Date.now()}`;
  await page.goto("/");
  await page.getByLabel("Task name").fill(name);
  await page.getByLabel("Prompt").fill("Name the capital of Nigeria and answer in one short sentence of plain text.");
  await page.getByRole("button", { name: "Add check" }).click();
  await page.getByLabel("Check value").first().fill("Mock answer");
  await page.getByRole("button", { name: "Save task" }).click();

  await page.getByRole("link", { name }).click();
  await page.getByLabel("Models").fill("mock:echo, mock:empty");
  await page.getByRole("button", { name: "Run on models" }).click();

  const echo = page.getByRole("row", { name: /mock:echo/ });
  const empty = page.getByRole("row", { name: /mock:empty/ });
  await expect(echo).toContainText("100%", { timeout: 15_000 });
  await expect(empty).toContainText("0%", { timeout: 15_000 });

  await page.getByRole("link", { name: "Benchmarks" }).click();
  await expect(page.getByRole("row", { name: /mock:echo/ })).toBeVisible();
});
