import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("CultureShift foundation page", () => {
  it("renders both static fixtures for human review", () => {
    const { container } = render(<Home />);

    expect(
      screen.getByRole("heading", { name: "CultureShift bilateral fixture lab" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "China to UK" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "UK to China" }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(2);
    expect(screen.getByRole("article", { name: /China to UK/ })).toBeInTheDocument();
    expect(screen.getByRole("article", { name: /UK to China/ })).toBeInTheDocument();
    expect(screen.getAllByText("Fixture Demo / 非实时模型")).toHaveLength(2);
    expect(screen.getAllByText("Human review required")).toHaveLength(2);

    expect(
      container.querySelectorAll(
        'button, input[type="file"], form, [contenteditable]:not([contenteditable="false"])',
      ),
    ).toHaveLength(0);
    expect(container.textContent).not.toMatch(
      /live[ -]?model|performance[ -]?uplift|approval|approved (?:for|by|as)/i,
    );
  });
});
