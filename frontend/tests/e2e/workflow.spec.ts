import { test, expect } from "@playwright/test";
test("login page renders with accessible authentication fields", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await expect(page.getByLabel("Email address")).toBeVisible();
  await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("button", { name: "Sign in to workspace" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
test("real authenticated inventory, evidence, assessment, guardrail and tenant isolation workflow", async ({
  page,
}) => {
  test.setTimeout(90000);
  test.skip(
    !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
    "Set E2E_EMAIL and E2E_PASSWORD to an isolated test tenant's administrator credentials.",
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
    .fill(`Browser test ${suffix}`);
  await page.getByLabel("System owner").fill("E2E test");
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(
    page.getByRole("cell", { name: `Browser test ${suffix}`, exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Evidence library", exact: true })
    .click();
  await page.getByRole("button", { name: "Add evidence" }).click();
  await page
    .getByLabel("Evidence title", { exact: true })
    .fill(`Test evidence ${suffix}`);
  await page
    .getByLabel("Artifact content", { exact: true })
    .fill("Synthetic browser test evidence. No real personal data.");
  await page.getByRole("button", { name: "Save record" }).click();
  const row = page
    .getByRole("row")
    .filter({ hasText: `Test evidence ${suffix}` });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Verify", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  if (process.env.E2E_SIGNING_ENABLED === "1") {
    await row.getByRole("button", { name: "Attest", exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("Ed25519");
    await page.getByRole("button", { name: "Close dialog" }).click();
    await row.getByRole("button", { name: "Verify", exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText(
      '"signature_valid": true',
    );
    await page.getByRole("button", { name: "Close dialog" }).click();
  }
  for (const framework of ["EU AI Act", "ISO / IEC 42001", "NIST AI RMF"]) {
    await page.getByRole("link", { name: framework, exact: true }).click();
    await expect(
      page.getByRole("heading", {
        name:
          framework === "ISO / IEC 42001"
            ? "ISO/IEC 42001 workspace"
            : `${framework} workspace`,
        exact: true,
      }),
    ).toBeVisible();
    await page.getByRole("button", { name: "New assessment" }).click();
    await page
      .getByLabel("Assessment name", { exact: true })
      .fill(`${framework} browser assessment ${suffix}`);
    await page
      .getByLabel("AI system", { exact: true })
      .selectOption({ label: `Browser test ${suffix}` });
    await page.getByRole("button", { name: "Save record" }).click();
    await page
      .getByRole("button", { name: "Evaluate", exact: true })
      .first()
      .click();
    await page
      .getByLabel("Control status", { exact: true })
      .selectOption("implemented");
    await page
      .getByLabel("Assessment and applicability notes", { exact: true })
      .fill("Synthetic browser validation of control persistence.");
    const help = await page
      .getByLabel("Evidence IDs (JSON array)", { exact: true })
      .locator("..")
      .locator("small")
      .innerText();
    const evidenceId = help.match(
      new RegExp(`Test evidence ${suffix}: ([a-f0-9-]+)`),
    )?.[1];
    expect(evidenceId).toBeTruthy();
    await page
      .getByLabel("Evidence IDs (JSON array)", { exact: true })
      .fill(JSON.stringify([evidenceId]));
    await page.getByRole("button", { name: "Save record" }).click();
    await expect(page.getByRole("dialog")).toHaveCount(1);
    await expect(
      page.getByRole("dialog").getByText("implemented", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Close dialog" }).click();
  }
  await page.getByRole("link", { name: "LLM guardrails", exact: true }).click();
  await page.getByRole("button", { name: "Create policy" }).click();
  await page
    .getByLabel("Policy name", { exact: true })
    .fill(`E2E policy ${suffix}`);
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(
    page.getByRole("heading", { name: `E2E policy ${suffix}` }),
  ).toBeVisible();
  await page
    .getByLabel("Policy", { exact: true })
    .selectOption({ label: `E2E policy ${suffix}` });
  await page
    .getByLabel("Test input", { exact: true })
    .fill("Contact test@example.com for synthetic evaluation.");
  await page.getByRole("button", { name: "Evaluate request" }).click();
  await expect(
    page.getByRole("heading", { name: "Processed output" }),
  ).toBeVisible();
  await expect(page.locator(".guardrail-result")).not.toContainText(
    "test@example.com",
  );
  await page.getByRole("link", { name: "Audit trail", exact: true }).click();
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page.screenshot({
    path: "test-results/authenticated-audit.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Governance overview" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/dashboard-desktop.png",
    fullPage: true,
  });
  const firstTenant = await page.getByLabel("Select workspace").inputValue();
  await page
    .getByRole("link", { name: "Organisation & access", exact: true })
    .click();
  await page.getByRole("button", { name: "Create organisation" }).click();
  await page
    .getByLabel("Organisation name", { exact: true })
    .fill(`Isolated tenant ${suffix}`);
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByRole("status")).toContainText("Organisation created");
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByLabel("Email address").fill(process.env.E2E_EMAIL!);
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await page
    .getByLabel("Select workspace")
    .selectOption({ label: `Isolated tenant ${suffix}` });
  await page.getByRole("link", { name: "AI systems", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "No AI systems yet" }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: `Browser test ${suffix}`, exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Select workspace").selectOption(firstTenant);
  await expect(
    page.getByRole("cell", { name: `Browser test ${suffix}`, exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    )
    .toBe(true);
  await page.screenshot({
    path: "test-results/inventory-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
});

test("every workspace page loads real data without browser or API errors", async ({
  page,
}) => {
  test.skip(
    !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
    "Authenticated test credentials are required.",
  );
  test.setTimeout(90000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.url().includes(":8100/api/v1/") && response.status() >= 400)
      errors.push(`${response.status()} ${response.url()}`);
  });
  await page.goto("/");
  await page.getByLabel("Email address").fill(process.env.E2E_EMAIL!);
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Governance overview" }),
  ).toBeVisible();
  const links = page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link");
  const names = await links.allTextContents();
  expect(names.length).toBe(21);
  for (let index = 0; index < names.length; index++) {
    await links.nth(index).click();
    await expect(page.locator("#main-content h1")).toBeVisible();
    await expect(page.locator("#main-content").getByRole("alert")).toHaveCount(
      0,
    );
    await expect(
      page.getByRole("status").filter({ hasText: "Loading workspace data" }),
    ).toHaveCount(0);
  }
  expect(errors).toEqual([]);
});
