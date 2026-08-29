import { expect, type Download, type Page, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const sourceFixture = resolve(
  process.cwd(),
  "public/fixtures/orbit-ai/orbit-ai-product-ui.png",
);
const capabilityPattern = /[A-Za-z0-9_-]{40,}\.[A-Za-z0-9_-]{32,}/;
const publicCompositionKeys = [
  "artifact_id",
  "disclosure",
  "execution_mode",
  "generated_at",
  "height",
  "layers",
  "media_type",
  "rendered_sha256",
  "run_id",
  "status",
  "width",
];

async function startUpload(page: Page, direction: "China to UK" | "UK to China") {
  await page.goto("/studio");
  await page.getByLabel(direction).check();
  await page.getByLabel("Source ad").setInputFiles(sourceFixture);
  await page.getByLabel("Provenance reference").fill("public:orbit-ai-fixture-source");
  await page.getByLabel("Rights reference").fill("public:demo-assets-rights");
  await page.getByLabel("I have authority to process this source.").check();
  await page.getByRole("button", { name: "Upload and start" }).click();
}

async function configure(page: Page, direction: "China to UK" | "UK to China") {
  await startUpload(page, direction);
  await expect(page.getByRole("heading", { name: "Confirm Brand Lock" })).toBeVisible();
}

async function reachVersionOne(page: Page, direction: "China to UK" | "UK to China") {
  await configure(page, direction);
  await page.getByRole("button", { name: "Confirm Brand Lock" }).click();
  await expect(page.getByText("Brand Lock confirmed and immutable.")).toBeVisible();
  await page.getByRole("button", { name: "Generate fixture proposal" }).click();
  await expect(page.getByRole("heading", { name: "Version 1" })).toBeVisible({
    timeout: 30_000,
  });
}

async function download(page: Page, name: string): Promise<Download> {
  const pending = page.waitForEvent("download");
  await page.getByRole("button", { name }).click();
  return pending;
}

async function verifyPng(file: Download, version: 1 | 2) {
  expect(file.suggestedFilename()).toBe(`cultureshift-version-${version}.png`);
  expect(file.suggestedFilename()).not.toMatch(capabilityPattern);
  const path = await file.path();
  expect(path).not.toBeNull();
  const bytes = await readFile(path!);
  expect(bytes.length).toBeGreaterThan(1_000);
  expect(bytes.subarray(1, 4).toString("ascii")).toBe("PNG");
  expect(bytes.readUInt32BE(16)).toBe(1600);
  expect(bytes.readUInt32BE(20)).toBe(900);
}

async function verifyJson(file: Download, version: 1 | 2) {
  expect(file.suggestedFilename()).toBe(`cultureshift-version-${version}.json`);
  expect(file.suggestedFilename()).not.toMatch(capabilityPattern);
  const path = await file.path();
  expect(path).not.toBeNull();
  const bytes = await readFile(path!);
  expect(bytes.length).toBeGreaterThan(100);
  expect(bytes.length).toBeLessThan(32_000);
  const text = bytes.toString("utf8");
  expect(text).not.toMatch(capabilityPattern);
  const value = JSON.parse(text) as Record<string, unknown>;
  expect(Object.keys(value).sort()).toEqual(publicCompositionKeys);
  expect(value.width).toBe(1600);
  expect(value.height).toBe(900);
  expect(value.media_type).toBe("image/png");
  return value;
}

async function verifyBrowserTokenBoundary(page: Page) {
  expect(page.url()).not.toMatch(capabilityPattern);
  expect(await page.locator("body").innerText()).not.toMatch(capabilityPattern);
  expect(await page.evaluate(() => Object.values(localStorage))).toEqual([]);
  expect(await page.evaluate(() => Object.values(sessionStorage))).toEqual([]);
  const cookies = await page.context().cookies();
  expect(JSON.stringify(cookies)).not.toMatch(capabilityPattern);
}

for (const direction of ["China to UK", "UK to China"] as const) {
  test(`${direction} completes Version 1, exports, deletes, and resets`, async ({ page }) => {
    await reachVersionOne(page, direction);
    await verifyPng(await download(page, "Export version 1 PNG"), 1);
    await verifyJson(await download(page, "Export version 1 JSON"), 1);
    await verifyBrowserTokenBoundary(page);
    await page.getByRole("button", { name: "Delete uploaded source and reset" }).click();
    await expect(page.getByText("Only the uploaded source asset was deleted")).toBeVisible();
    await expect(page.getByRole("button", { name: "Upload and start" })).toBeDisabled();
    await expect(page.getByRole("heading", { name: "Version 1" })).toHaveCount(0);
  });
}

test("one structured revision preserves Version 1 and creates no Version 3", async ({ page }) => {
  await reachVersionOne(page, "China to UK");
  const versionOne = await verifyJson(await download(page, "Export version 1 JSON"), 1);
  await page.getByLabel("Shorten headline").check();
  await page.getByLabel("Feedback context").fill("Use the allowed structured shortening only.");
  await page.getByRole("button", { name: "Create version 2" }).click();
  await expect(page.getByRole("heading", { name: "Compare versions" })).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByRole("heading", { name: "Version 1" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Version 2" })).toBeVisible();
  const versionTwo = await verifyJson(await download(page, "Export version 2 JSON"), 2);
  await verifyPng(await download(page, "Export version 1 PNG"), 1);
  await verifyPng(await download(page, "Export version 2 PNG"), 2);
  expect(versionTwo.artifact_id).not.toBe(versionOne.artifact_id);
  expect(versionTwo.run_id).toBe(versionOne.run_id);
  expect(versionTwo.disclosure).toBe(versionOne.disclosure);
  expect(versionTwo.width).toBe(versionOne.width);
  expect(versionTwo.height).toBe(versionOne.height);
  const lockedLayers = (value: Record<string, unknown>) =>
    (value.layers as Array<Record<string, unknown>>)
      .filter((layer) => ["logo", "product_ui"].includes(String(layer.kind)))
      .map(({ kind, source_asset_id, bounds }) => ({ kind, source_asset_id, bounds }));
  expect(lockedLayers(versionTwo)).toEqual(lockedLayers(versionOne));
  await expect(page.getByRole("button", { name: "Create version 2" })).toHaveCount(0);
  await expect(page.getByText(/Version 3/i)).toHaveCount(0);
  await verifyBrowserTokenBoundary(page);
});

test("upload validation and authority fail closed before network work", async ({ page }) => {
  await page.goto("/studio");
  await page.getByLabel("Source ad").setInputFiles({
    name: "unsupported.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("not an image"),
  });
  await expect(page.getByRole("alert")).toContainText("Choose a PNG, JPEG, or WebP");
  await expect(page.getByRole("button", { name: "Upload and start" })).toBeDisabled();
  await page.getByLabel("Source ad").setInputFiles(sourceFixture);
  await page.getByLabel("Provenance reference").fill("public:orbit-ai-fixture-source");
  await page.getByLabel("Rights reference").fill("public:demo-assets-rights");
  await expect(page.getByRole("button", { name: "Upload and start" })).toBeDisabled();
});

test("bounded capability, conflict, retryable, final, and export failures stay distinct", async ({ page }) => {
  await page.route("**/api/v1/runs/*/analyze", async (route) => {
    await route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({ detail: { code: "capability_subject_mismatch" } }),
    });
  });
  await startUpload(page, "China to UK");
  await expect(page.getByRole("alert")).toContainText("capability_subject_mismatch");
  await expect(page.getByRole("alert")).not.toContainText(capabilityPattern);

  await page.unrouteAll();
  await page.reload();
  await configure(page, "China to UK");
  await page.route("**/api/v1/runs/*/brand-lock/confirm", async (route) => {
    await route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({ detail: { code: "locked_field_changed" } }) });
  });
  await page.getByRole("button", { name: "Confirm Brand Lock" }).click();
  await expect(page.getByText("Unable to confirm Brand Lock.")).toBeVisible();
  await expect(page.getByText(/locked_field_changed/)).toBeVisible();

  await page.unrouteAll();
  await page.reload();
  await reachVersionOne(page, "China to UK");
  await page.route("**/api/v1/runs/*/composition.png?result_version=1", async (route) => {
    await route.fulfill({ status: 410, contentType: "application/json", body: JSON.stringify({ detail: { code: "composition_artifact_unavailable" } }) });
  });
  await page.getByRole("button", { name: "Export version 1 PNG" }).click();
  await expect(page.getByRole("alert")).toContainText("composition_artifact_unavailable");
  await expect(page.getByRole("button", { name: /Retry version 2/ })).toHaveCount(0);
});

test("retry is visible only for server-authorized revision failure", async ({ page }) => {
  await reachVersionOne(page, "UK to China");
  await page.getByLabel("Shorten body").check();
  await page.getByLabel("Feedback context").fill("Use the allowed structured shortening only.");
  await page.route("**/api/v1/runs/*/feedback", async (route) => {
    await route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ detail: { code: "revision_failed" } }) });
  });
  await page.getByRole("button", { name: "Create version 2" }).click();
  await expect(page.getByRole("button", { name: "Retry version 2" })).toBeVisible();
  await expect(page.getByText(/Version 3/i)).toHaveCount(0);

  await page.unrouteAll();
  await page.reload();
  await reachVersionOne(page, "UK to China");
  await page.getByLabel("Shorten body").check();
  await page.getByLabel("Feedback context").fill("Use the allowed structured shortening only.");
  await page.route("**/api/v1/runs/*/feedback", async (route) => {
    await route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({ detail: { code: "revision_limit_reached" } }) });
  });
  await page.getByRole("button", { name: "Create version 2" }).click();
  await expect(page.getByRole("alert")).toContainText("revision_limit_reached");
  await expect(page.getByRole("button", { name: "Retry version 2" })).toHaveCount(0);
});
