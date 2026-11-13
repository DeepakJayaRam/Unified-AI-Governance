import { test, expect } from "@playwright/test";

test("risk, finding, corrective action, settings and discovery forms persist", async ({
  page,
}) => {
  test.setTimeout(90000);
  test.skip(
    !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
    "Requires isolated real identity",
  );
  await page.goto("/");
  await page.getByLabel("Email address").fill(process.env.E2E_EMAIL!);
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Governance overview" }),
  ).toBeVisible();
  const suffix = Date.now();
  for (const [link, singular] of [
    ["Risk register", "risk"],
    ["Findings", "finding"],
    ["Corrective actions", "corrective action"],
  ]) {
    await page.getByRole("link", { name: link, exact: true }).click();
    await page
      .getByRole("button", { name: "Add " + singular, exact: true })
      .click();
    const title = `Release_${singular}_${suffix}`;
    await page.getByLabel("Title", { exact: true }).fill(title);
    await page
      .getByLabel("Description", { exact: true })
      .fill("Synthetic review and treatment");
    await page.getByLabel("Owner", { exact: true }).fill("Synthetic owner");
    await page.getByLabel("Due date", { exact: true }).fill("2026-12-01");
    await page.getByRole("button", { name: "Save record" }).click();
    const row = page.getByRole("row").filter({ hasText: title });
    await expect(row).toContainText("Synthetic owner");
    await row.getByRole("button", { name: "Edit", exact: true }).click();
    await page.getByLabel("Status", { exact: true }).selectOption("resolved");
    await page.getByRole("button", { name: "Save record" }).click();
    await expect(row).toContainText("resolved");
    await row.getByRole("button", { name: "Details", exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("2026-12-01");
    await page.getByRole("button", { name: "Close dialog" }).click();
  }
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await page
    .getByLabel("Workspace display name")
    .fill("Release browser workspace");
  await page.getByLabel("Retention days").fill("365");
  await page.getByRole("button", { name: "Save settings" }).click();
  await expect(
    page.getByText("Workspace settings saved.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Integration settings", exact: true })
    .click();
  const card = page.locator(".integration-card").filter({
    has: page.getByRole("heading", { name: "OWASP cdxgen", exact: true }),
  });
  await card.getByRole("button", { name: "Configure", exact: true }).click();
  await page.getByLabel("Enable integration").check();
  await page.getByRole("button", { name: "Save configuration" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("link", { name: "Discovery scans", exact: true })
    .click();
  await page
    .getByLabel("AI system", { exact: true })
    .selectOption({ index: 1 });
  await page
    .getByLabel("Discovery integration", { exact: true })
    .selectOption("cdxgen");
  const submitted = page.waitForResponse(
    (r) => r.url().endsWith("/executions") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Queue scan" }).click();
  expect((await submitted).status()).toBe(202);
  await page
    .getByRole("link", { name: "Execution history", exact: true })
    .click();
  const job = page.getByRole("row").filter({ hasText: "cdxgen" }).first();
  await expect(job).toContainText("succeeded", { timeout: 30000 });
  await job.getByRole("button", { name: "View results" }).click();
  await expect(page.getByRole("dialog")).toContainText("CycloneDX");
});
