import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Table } from "../../src/components/ui";

test("mobile inventory table contains horizontal overflow and keeps actions reachable", async ({
  page,
}) => {
  const css = readFileSync(resolve("src/app/globals.css"), "utf8");
  const rows = [
    {
      id: "fixture-1",
      name: "Synthetic responsive-layout test system",
      owner: "Layout test",
      risk_level: "unassessed",
      created_at: "2026-11-13T06:00:00+00:00",
    },
  ];
  const table = renderToStaticMarkup(
    createElement(Table, {
      rows,
      columns: [
        { key: "name", title: "System" },
        { key: "owner", title: "Owner" },
        { key: "risk_level", title: "Risk level", badge: true },
        { key: "created_at", title: "Registered" },
      ],
      actions: () =>
        createElement("button", { className: "text-button" }, "Details"),
    }),
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.setContent(
    `<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>${css}</style></head><body><div class="app-shell"><div class="main-shell"><header class="topbar"><strong>Layout regression fixture</strong></header><main class="main-content"><header class="page-heading"><div><p class="eyebrow">Responsive verification</p><h1>AI system inventory</h1><p>Synthetic fixture rendered by the actual Table component.</p></div></header><section class="panel"><div class="panel-title"><h2>Inventory records</h2></div>${table}</section></main></div></div></body></html>`,
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    390,
  );
  const scroll = page.locator(".table-scroll");
  expect(await scroll.evaluate((el) => el.scrollWidth > el.clientWidth)).toBe(
    true,
  );
  await scroll.evaluate((el) => {
    el.scrollLeft = el.scrollWidth;
  });
  await expect(page.getByRole("button", { name: "Details" })).toBeInViewport();
  await page.screenshot({
    path: "test-results/mobile-layout-regression.png",
    fullPage: true,
  });
});
