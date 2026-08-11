import { describe, expect, it } from "vitest";

import type { RunStatus } from "./contracts";

describe("generated contracts", () => {
  it("exposes the public run status contract", () => {
    const status: RunStatus = "pending";
    expect(status).toBe("pending");
  });
});
