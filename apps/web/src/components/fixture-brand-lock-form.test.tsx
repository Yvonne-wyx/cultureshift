import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { loadFixture } from "../fixtures/fixture-loader";

import { FixtureBrandLockForm } from "./fixture-brand-lock-form";

describe("FixtureBrandLockForm", () => {
  it.each(["china-to-uk", "uk-to-china"] as const)(
    "confirms %s offline with explicit fixture disclosure",
    async (fixtureId) => {
      render(<FixtureBrandLockForm fixture={loadFixture(fixtureId)} />);

      expect(screen.getByText("Fixture confirmation only")).toBeInTheDocument();
      fireEvent.click(screen.getByRole("checkbox", { name: /become immutable/i }));
      fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));
      expect(await screen.findByText(/Brand Lock confirmed and immutable/)).toBeInTheDocument();
      expect(screen.getByText("in_progress")).toBeInTheDocument();
    },
  );
});
