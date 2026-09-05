import { spawn } from "node:child_process";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import net from "node:net";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = resolve(webRoot, "../..");
const DEFAULT_SECRET = "day18-local-fixture-secret-not-for-production";

export function parseDemoConfig(argv = process.argv.slice(2), environment = process.env) {
  const valueAfter = (name) => {
    const index = argv.indexOf(name);
    return index === -1 ? undefined : argv[index + 1];
  };
  const backendPort = Number(valueAfter("--backend-port") ?? environment.CULTURESHIFT_DEMO_BACKEND_PORT ?? 8000);
  const frontendPort = Number(valueAfter("--frontend-port") ?? environment.CULTURESHIFT_DEMO_FRONTEND_PORT ?? 3000);
  const secret = environment.CULTURESHIFT_CAPABILITY_SECRET ?? DEFAULT_SECRET;
  if (![backendPort, frontendPort].every((port) => Number.isInteger(port) && port > 0 && port <= 65535)) {
    throw new Error("Demo ports must be integers from 1 to 65535.");
  }
  if (backendPort === frontendPort) throw new Error("Demo ports must be different.");
  if (secret.length < 32 || /production/i.test(environment.NODE_ENV ?? "")) {
    throw new Error("Demo requires a non-production capability secret of at least 32 characters.");
  }
  return {
    backendPort,
    frontendPort,
    secret,
    checkOnly: argv.includes("--check"),
    requestedRoot: valueAfter("--root") ?? environment.CULTURESHIFT_DEMO_ROOT,
  };
}

export async function assertPortAvailable(port) {
  await new Promise((resolvePromise, reject) => {
    const server = net.createServer();
    server.unref();
    server.once("error", () => reject(new Error(`Loopback port ${port} is unavailable.`)));
    server.listen({ host: "127.0.0.1", port }, () => server.close(resolvePromise));
  });
}

async function waitFor(url, child, label) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`${label} exited before readiness.`);
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Readiness errors are intentionally not exposed.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 250));
  }
  throw new Error(`${label} readiness timed out.`);
}

function launch(command, args, options, children) {
  const child = spawn(command, args, {
    stdio: ["ignore", "inherit", "inherit"],
    detached: process.platform !== "win32",
    ...options,
  });
  children.add(child);
  child.once("exit", () => children.delete(child));
  return child;
}

export async function runDemo(argv = process.argv.slice(2), environment = process.env) {
  const config = parseDemoConfig(argv, environment);
  await assertPortAvailable(config.backendPort);
  await assertPortAvailable(config.frontendPort);
  if (config.checkOnly) {
    console.log("Demo configuration and loopback ports are available.");
    return;
  }

  const ownsRoot = !config.requestedRoot;
  const root = config.requestedRoot
    ? resolve(config.requestedRoot)
    : await mkdtemp(resolve(tmpdir(), "cultureshift-day18-demo-"));
  const assetRoot = resolve(root, "assets");
  await mkdir(resolve(root, ".cultureshift"), { recursive: true });
  await mkdir(assetRoot, { recursive: true });
  const children = new Set();
  let stopping = false;
  const stop = async () => {
    if (stopping) return;
    stopping = true;
    for (const child of children) {
      if (child.exitCode === null) {
        if (process.platform === "win32") child.kill("SIGTERM");
        else process.kill(-child.pid, "SIGTERM");
      }
    }
    await Promise.all([...children].map((child) => new Promise((done) => {
      child.once("exit", done);
      setTimeout(done, 5_000);
    })));
    if (ownsRoot) await rm(root, { recursive: true, force: true });
  };
  for (const signal of ["SIGINT", "SIGTERM"]) process.once(signal, async () => {
    await stop();
    process.exit(0);
  });

  try {
    const backend = launch(
      environment.CULTURESHIFT_DEMO_PYTHON ?? "python3",
      ["-m", "uvicorn", "cultureshift.app:app", "--host", "127.0.0.1", "--port", String(config.backendPort), "--no-access-log"],
      {
        cwd: repositoryRoot,
        env: {
          ...environment,
          CULTURESHIFT_CAPABILITY_SECRET: config.secret,
          CULTURESHIFT_TEMP_ASSET_DIR: assetRoot,
          CULTURESHIFT_STUDIO_ORIGINS: `http://127.0.0.1:${config.frontendPort}`,
        },
      },
      children,
    );
    await waitFor(`http://127.0.0.1:${config.backendPort}/openapi.json`, backend, "Backend");
    console.log(`Backend ready on http://127.0.0.1:${config.backendPort}`);

    const frontendEnvironment = {
      ...environment,
      NEXT_TELEMETRY_DISABLED: "1",
      NEXT_PUBLIC_CULTURESHIFT_API_URL: `http://127.0.0.1:${config.backendPort}`,
    };
    const build = launch(process.execPath, [resolve(webRoot, "node_modules/next/dist/bin/next"), "build", "--webpack"], { cwd: webRoot, env: frontendEnvironment }, children);
    const buildCode = await new Promise((done) => build.once("exit", (code) => done(code ?? 1)));
    if (buildCode !== 0) throw new Error("Frontend build failed.");
    const frontend = launch(process.execPath, [resolve(webRoot, "node_modules/next/dist/bin/next"), "start", "--hostname", "127.0.0.1", "--port", String(config.frontendPort)], { cwd: webRoot, env: frontendEnvironment }, children);
    await waitFor(`http://127.0.0.1:${config.frontendPort}/studio`, frontend, "Studio");
    console.log(`Studio ready on http://127.0.0.1:${config.frontendPort}/studio`);
    await new Promise((done) => frontend.once("exit", done));
  } finally {
    await stop();
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  runDemo().catch((error) => {
    console.error(error instanceof Error ? error.message : "Demo launcher failed safely.");
    process.exitCode = 1;
  });
}
