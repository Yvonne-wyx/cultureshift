import { spawn } from "node:child_process";
import { mkdtemp, mkdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const temporaryRoot = await mkdtemp(resolve(tmpdir(), "cultureshift-e2e-"));
const assetRoot = resolve(temporaryRoot, "assets");
const outputRoot = resolve(temporaryRoot, "playwright");
await mkdir(resolve(temporaryRoot, ".cultureshift"), { recursive: true });
await mkdir(assetRoot, { recursive: true });

const python = process.env.CULTURESHIFT_E2E_PYTHON ?? "python3";
const node = process.execPath;
const children = new Set();
let stopping = false;

function start(command, args, options) {
  const child = spawn(command, args, {
    stdio: ["ignore", "inherit", "inherit"],
    detached: process.platform !== "win32",
    ...options,
  });
  children.add(child);
  child.once("exit", () => children.delete(child));
  return child;
}

async function waitFor(url, child, label) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`${label} exited before readiness`);
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Readiness polling deliberately exposes no response or exception detail.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 250));
  }
  throw new Error(`${label} did not become ready`);
}

async function stop() {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (child.exitCode === null) {
      if (process.platform === "win32") child.kill("SIGTERM");
      else process.kill(-child.pid, "SIGTERM");
    }
  }
  await Promise.all(
    [...children].map(
      (child) =>
        new Promise((resolvePromise) => {
          child.once("exit", resolvePromise);
          setTimeout(resolvePromise, 5_000);
        }),
    ),
  );
  await rm(temporaryRoot, { recursive: true, force: true });
}

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, async () => {
    await stop();
    process.exit(1);
  });
}

let exitCode = 1;
try {
  const frontendEnvironment = {
    ...process.env,
    NEXT_TELEMETRY_DISABLED: "1",
    NEXT_PUBLIC_CULTURESHIFT_API_URL: "http://127.0.0.1:8000",
  };
  const build = start(
    node,
    [resolve(webRoot, "node_modules/next/dist/bin/next"), "build", "--webpack"],
    { cwd: webRoot, env: frontendEnvironment },
  );
  const buildExit = await new Promise((resolvePromise) =>
    build.once("exit", (code) => resolvePromise(code ?? 1)),
  );
  if (buildExit !== 0) throw new Error("frontend build failed");

  const backend = start(
    python,
    [
      "-m",
      "uvicorn",
      "cultureshift.app:app",
      "--host",
      "127.0.0.1",
      "--port",
      "8000",
      "--no-access-log",
    ],
    {
      cwd: temporaryRoot,
      env: {
        ...process.env,
        CULTURESHIFT_CAPABILITY_SECRET:
          "day17-browser-fixture-secret-not-for-production",
        CULTURESHIFT_TEMP_ASSET_DIR: assetRoot,
        CULTURESHIFT_STUDIO_ORIGINS: "http://127.0.0.1:3000",
      },
    },
  );
  const frontend = start(
    node,
    [resolve(webRoot, "node_modules/next/dist/bin/next"), "start", "--hostname", "127.0.0.1", "--port", "3000"],
    {
      cwd: webRoot,
      env: frontendEnvironment,
    },
  );
  await Promise.all([
    waitFor("http://127.0.0.1:8000/openapi.json", backend, "backend"),
    waitFor("http://127.0.0.1:3000/studio", frontend, "frontend"),
  ]);

  const testProcess = start(
    node,
    [resolve(webRoot, "node_modules/@playwright/test/cli.js"), "test", ...process.argv.slice(2)],
    {
      cwd: webRoot,
      env: { ...process.env, CULTURESHIFT_E2E_OUTPUT_DIR: outputRoot },
    },
  );
  exitCode = await new Promise((resolvePromise) =>
    testProcess.once("exit", (code) => resolvePromise(code ?? 1)),
  );
} catch {
  console.error("Browser E2E infrastructure failed safely.");
} finally {
  await stop();
}

process.exit(exitCode);
