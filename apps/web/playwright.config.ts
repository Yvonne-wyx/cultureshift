import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e/specs",
  outputDir:
    process.env.CULTURESHIFT_E2E_OUTPUT_DIR ?? "/tmp/cultureshift-e2e-results",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  forbidOnly: true,
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:3000",
    acceptDownloads: true,
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [
    {
      name: "chromium",
      use: {
        browserName: "chromium",
        launchOptions: process.env.CULTURESHIFT_E2E_CHROME_PATH
          ? { executablePath: process.env.CULTURESHIFT_E2E_CHROME_PATH }
          : {},
      },
    },
  ],
});
