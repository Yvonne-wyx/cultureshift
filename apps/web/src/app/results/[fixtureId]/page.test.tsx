import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ResultPage, { generateStaticParams } from "./page";

describe("fixture result page", () => {
  it("pre-renders both fixture routes", () => {
    expect(generateStaticParams()).toEqual([
      { fixtureId: "china-to-uk" },
      { fixtureId: "uk-to-china" },
    ]);
  });

  it.each(["china-to-uk", "uk-to-china"] as const)(
    "renders the complete %s result and walkthrough",
    async (fixtureId) => {
      render(await ResultPage({ params: Promise.resolve({ fixtureId }) }));

      expect(screen.getAllByText("Fixture Demo / 非实时模型")).toHaveLength(1);
      expect(screen.getByRole("heading", { name: "Localized fixture result" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Brand Lock" })).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: "Brand Lock confirmation preparation" }),
      ).toBeInTheDocument();
      expect(screen.getByText("awaiting_brand_lock")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Confirm Brand Lock — available Day 10" }),
      ).toBeDisabled();
      expect(screen.getByRole("heading", { name: "Traceability" })).toBeInTheDocument();
      expect(screen.getByText("1. Review source")).toBeInTheDocument();
      expect(screen.getByText("2. Inspect proposal")).toBeInTheDocument();
      expect(screen.getByText("3. Verify traceability")).toBeInTheDocument();
      expect(screen.getByText("Pending review")).toBeInTheDocument();
      expect(screen.getAllByText("Human review required")).toHaveLength(2);
    },
  );
});
