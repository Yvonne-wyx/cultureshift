import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { loadFixture } from "../fixtures/fixture-loader";

import { CompositionEvidence } from "./composition-evidence";

describe("CompositionEvidence", () => {
  it.each(["china-to-uk", "uk-to-china"] as const)(
    "shows bounded deterministic evidence for %s",
    (fixtureId) => {
      const composition = loadFixture(fixtureId).composition;
      const { container } = render(<CompositionEvidence composition={composition} />);

      expect(
        screen.getByRole("heading", { name: "Deterministic composition / 确定性合成" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("img", { name: "1600 x 900 fixture composition" }),
      ).toHaveAttribute("src", expect.stringContaining(encodeURIComponent(composition.preview_path)));
      expect(screen.getByText("Fixture Demo / 非实时模型")).toBeInTheDocument();
      expect(screen.getByText(/NotoSansCJKsc-Regular\.otf/)).toBeInTheDocument();
      expect(screen.getByText(composition.rendered_sha256)).toBeInTheDocument();
      expect(screen.getAllByText(/human review required/i)).toHaveLength(2);
      expect(container.textContent).not.toMatch(
        /live model|culturally validated|approved for production|capability[_ -]?token|[a-z]:\\/i,
      );
    },
  );
});
