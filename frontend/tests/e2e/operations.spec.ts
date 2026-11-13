import { test, expect, Page } from "@playwright/test";
import { randomBytes } from "node:crypto";

async function login(page: Page, email: string, password: string) {
  await page.goto("/");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Governance overview" }),
  ).toBeVisible();
}

test("integration enablement, health, real worker failure and retry are operable", async ({
  page,
}) => {
  test.setTimeout(90000);
  test.skip(
    !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
    "Requires isolated real identity",
  );
  await login(page, process.env.E2E_EMAIL!, process.env.E2E_PASSWORD!);
  await page.locator('a[href="/integration-config"]').click();
  const card = page.locator(".integration-card").filter({
    has: page.getByRole("heading", {
      name: "Compliance Trestle",
      exact: true,
    }),
  });
  await card.getByRole("button", { name: "Configure", exact: true }).click();
  await page.getByLabel("Enable integration").check();
  await page.getByRole("button", { name: "Save configuration" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await card.getByRole("button", { name: "Check connection" }).click();
  await expect(page.getByRole("dialog")).toContainText("Connected");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await card.getByRole("button", { name: "Configure", exact: true }).click();
  await page.getByLabel("Enable integration").uncheck();
  await page.getByRole("button", { name: "Save configuration" }).click();
  await expect(card).toContainText("Disabled");
  await expect(
    card.getByRole("button", { name: "Run", exact: true }),
  ).toHaveCount(0);
  await card.getByRole("button", { name: "Configure", exact: true }).click();
  await page.getByLabel("Enable integration").check();
  await page.getByRole("button", { name: "Save configuration" }).click();
  await card.getByRole("button", { name: "Run", exact: true }).click();
  await page
    .getByLabel("Execution input (JSON)")
    .fill('{"document":{"catalog":{}}}');
  const submitted = page.waitForResponse(
    (r) => r.url().endsWith("/executions") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Queue execution" }).click();
  expect((await submitted).status()).toBe(202);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.locator('a[href="/executions"]').click();
  const row = page
    .getByRole("row")
    .filter({ hasText: "compliance-trestle" })
    .first();
  await expect(row).toContainText("failed", { timeout: 30000 });
  await row.getByRole("button", { name: "View results" }).click();
  await expect(page.getByRole("dialog")).toContainText("invalid_oscal");
  await page.getByRole("button", { name: "Close dialog" }).click();
  const retried = page.waitForResponse((r) => r.url().endsWith("/retry"));
  await row.getByRole("button", { name: "Retry execution" }).click();
  expect((await retried).status()).toBe(202);
  await expect(
    page.getByRole("row").filter({ hasText: "compliance-trestle" }).first(),
  ).toContainText("failed", { timeout: 30000 });
});

test("membership roles, password rotation, denied writes and removal work through forms", async ({
  page,
  browser,
}) => {
  test.setTimeout(90000);
  test.skip(
    !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
    "Requires isolated real identity",
  );
  const email = `member-${randomBytes(6).toString("hex")}@test.invalid`;
  const password = randomBytes(24).toString("hex");
  const nextPassword = randomBytes(24).toString("hex");
  await login(page, process.env.E2E_EMAIL!, process.env.E2E_PASSWORD!);
  await page.locator('a[href="/organisation"]').click();
  await page.getByRole("button", { name: "Add member", exact: true }).click();
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Full name").fill("Synthetic member");
  await page.getByLabel("Initial password").fill(password);
  await page.getByLabel("Role", { exact: true }).selectOption("contributor");
  await page.getByRole("button", { name: "Save record" }).click();
  const row = page.getByRole("row").filter({ hasText: email });
  await expect(row).toContainText("contributor");
  await row.getByRole("button", { name: "Change role" }).click();
  await page.getByLabel("New role").selectOption("viewer");
  await page.getByRole("button", { name: "Update role" }).click();
  await expect(row).toContainText("viewer");
  const memberContext = await browser.newContext();
  const member = await memberContext.newPage();
  await login(member, email, password);
  await member.getByRole("link", { name: "AI systems", exact: true }).click();
  await member.getByRole("button", { name: "Add AI system" }).click();
  await member
    .getByLabel("System name", { exact: true })
    .fill("Denied viewer write");
  await member.getByRole("button", { name: "Save record" }).click();
  await expect(member.locator(".notice.error")).toContainText("read-only");
  await member.getByRole("button", { name: "Close dialog" }).click();
  await member.locator('a[href="/settings"]').click();
  await member.getByLabel("Current password").fill(password);
  await member.getByLabel("New password", { exact: true }).fill(nextPassword);
  await member
    .getByRole("button", { name: "Change password", exact: true })
    .click();
  await expect(
    member.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await login(member, email, nextPassword);
  await row.getByRole("button", { name: "Remove access" }).click();
  await page
    .getByRole("button", { name: "Remove workspace membership" })
    .click();
  await expect(row).toHaveCount(0);
  await member.getByRole("link", { name: "AI systems", exact: true }).click();
  await expect(member.locator(".notice.error")).toContainText(
    "Tenant membership required",
  );
  await memberContext.close();
});
