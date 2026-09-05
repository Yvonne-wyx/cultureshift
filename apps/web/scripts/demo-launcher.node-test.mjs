import assert from "node:assert/strict";
import net from "node:net";
import test from "node:test";

import { assertPortAvailable, parseDemoConfig } from "./demo-launcher.mjs";

test("parses bounded loopback demo configuration", () => {
  const config = parseDemoConfig(["--check", "--backend-port", "8123", "--frontend-port", "3123"], {});
  assert.equal(config.checkOnly, true);
  assert.equal(config.backendPort, 8123);
  assert.equal(config.frontendPort, 3123);
});

test("rejects production mode and conflicting ports", () => {
  assert.throws(() => parseDemoConfig([], { NODE_ENV: "production" }), /non-production/);
  assert.throws(() => parseDemoConfig(["--backend-port", "3000", "--frontend-port", "3000"], {}), /different/);
});

test("fails when a requested loopback port is already occupied", async () => {
  const server = net.createServer();
  await new Promise((done) => server.listen({ host: "127.0.0.1", port: 0 }, done));
  const address = server.address();
  assert.equal(typeof address, "object");
  await assert.rejects(() => assertPortAvailable(address.port), /unavailable/);
  await new Promise((done) => server.close(done));
});
