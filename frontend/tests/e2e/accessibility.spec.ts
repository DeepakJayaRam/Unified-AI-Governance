import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("login and all seven workspaces pass automated accessibility checks", async ({
  page,
}) => {
  test.setTimeout(120000);
  await page.goto("/");
  await expect(page).toHaveTitle("Unified AI Governance & Security");
  const violations = [
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ];
  test.skip(
    !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
    "Authenticated checks require an isolated identity",
  );
  await page.getByLabel("Email address").fill(process.env.E2E_EMAIL!);
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Governance overview" }),
  ).toBeVisible();
  for (const name of [
    "AI systems",
    "EU AI Act",
    "ISO / IEC 42001",
    "NIST AI RMF",
    "Evidence library",
    "Runtime monitoring",
    "LLM guardrails",
  ]) {
    await page.getByRole("link", { name, exact: true }).click();
    await expect(page.locator("main h1")).toBeVisible();
    await expect(
      page.getByText("Loading workspace data…", { exact: true }),
    ).toHaveCount(0);
    await expect(page).toHaveTitle("Unified AI Governance & Security");
    violations.push(
      (
        await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze()
      ).violations,
    );
  }
  expect(violations.flat()).toEqual([]);
});
