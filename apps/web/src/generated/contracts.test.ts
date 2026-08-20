import { describe, expect, expectTypeOf, it } from "vitest";

import type {
  BrandLockConfirmation,
  BrandLockConfirmed,
  RunStatus,
} from "./contracts";

describe("generated contracts", () => {
  it("exposes the public run status contract", () => {
    const status: RunStatus = "pending";
    expect(status).toBe("pending");
  });

  it("types an immutable Brand Lock confirmation response", () => {
    expectTypeOf<BrandLockConfirmation>().toHaveProperty("brand_lock");
    expectTypeOf<BrandLockConfirmed["status"]>().toEqualTypeOf<"in_progress">();
    expectTypeOf<BrandLockConfirmed>().toHaveProperty("confirmed_at");
  });
});
