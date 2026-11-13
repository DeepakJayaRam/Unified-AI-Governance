import { test, expect } from "@playwright/test";

test("governance decisions, policy rollback and human review use persisted APIs", async ({
  page,
}) => {
  test.setTimeout(90000);
  test.skip(
    !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
    "Requires an isolated real test identity",
  );
  const suffix = Date.now();
  await page.goto("/");
  await page.getByLabel("Email address").fill(process.env.E2E_EMAIL!);
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Governance overview" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "AI systems", exact: true }).click();
  await page.getByRole("button", { name: "Add AI system" }).click();
  await page
    .getByLabel("System name", { exact: true })
    .fill(`Governance workflow ${suffix}`);
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);

  for (const [link, kind] of [
    ["EU AI Act", "classification"],
    ["ISO / IEC 42001", "management_review"],
    ["NIST AI RMF", "risk_treatment"],
  ]) {
    await page.getByRole("link", { name: link, exact: true }).click();
    await page.getByRole("button", { name: "Add governance record" }).click();
    const dialog = page.getByRole("dialog");
    await dialog
      .getByLabel("Record title", { exact: true })
      .fill(`Decision ${kind} ${suffix}`);
    await dialog.getByLabel("Workflow", { exact: true }).selectOption(kind);
    await dialog
      .getByLabel("AI system", { exact: true })
      .selectOption({ label: `Governance workflow ${suffix}` });
    await dialog
      .getByLabel("Assessment rationale", { exact: true })
      .fill("Synthetic documented review for browser verification.");
    await dialog
      .getByLabel("Responsible owner", { exact: true })
      .fill("Test reviewer");
    await dialog.getByRole("button", { name: "Save record" }).click();
    await expect(dialog).toHaveCount(0);
    const row = page
      .getByRole("row")
      .filter({ hasText: `Decision ${kind} ${suffix}` });
    await expect(row).toBeVisible();
    await row.getByRole("button", { name: "Edit record", exact: true }).click();
    await page
      .getByLabel("Record status", { exact: true })
      .selectOption("approved");
    await page.getByRole("button", { name: "Save record" }).click();
    await expect(row).toContainText("approved");
  }

  await page.getByRole("link", { name: "LLM guardrails", exact: true }).click();
  await page
    .getByRole("button", { name: "Create policy", exact: true })
    .click();
  await page
    .getByLabel("Policy name", { exact: true })
    .fill(`Review policy ${suffix}`);
  await page.getByLabel("Policy configuration (JSON)", { exact: true }).fill(
    JSON.stringify({
      checks: ["native"],
      pii_action: "review",
      error_action: "block",
      blocked_terms: [],
    }),
  );
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const card = page
    .locator(".policy-card")
    .filter({ hasText: `Review policy ${suffix}` });
  await card.getByRole("button", { name: "Edit policy", exact: true }).click();
  await page.getByLabel("Policy configuration (JSON)", { exact: true }).fill(
    JSON.stringify({
      checks: ["native"],
      pii_action: "block",
      error_action: "block",
      blocked_terms: [],
    }),
  );
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await card.getByRole("button", { name: "Version history" }).click();
  await page.getByRole("button", { name: "Review rollback" }).click();
  await page.getByRole("button", { name: "Restore version 1" }).click();
  await expect(page.getByRole("status")).toContainText("Policy restored");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByLabel("Policy", { exact: true })
    .selectOption({ label: `Review policy ${suffix}` });
  await page
    .getByLabel("Test input", { exact: true })
    .fill("Synthetic review alice@example.invalid");
  await page.getByRole("button", { name: "Evaluate request" }).click();
  await expect(page.locator(".guardrail-result .badge")).toHaveText(/review/);
  await page
    .getByRole("link", { name: "Runtime monitoring", exact: true })
    .click();
  await page.getByRole("button", { name: "Resolve review" }).first().click();
  await page.getByLabel("Decision", { exact: true }).selectOption("block");
  await page
    .getByLabel("Review rationale", { exact: true })
    .fill("Synthetic reviewer requires redaction.");
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("cell", { name: "resolved", exact: true }).first(),
  ).toBeVisible();
});
