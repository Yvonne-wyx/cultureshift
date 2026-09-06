import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("CultureShift product landing page", () => {
  it("introduces the product and provides clear paths into the case study and demo", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { level: 1, name: "CultureShift" })).toBeInTheDocument();
    expect(
      screen.getByText("Human-in-the-Loop Cross-Cultural Creative Reasoning System"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start adapting" })).toHaveAttribute(
      "href",
      "/studio",
    );
    expect(screen.getByRole("link", { name: "Enter Studio" })).toHaveAttribute(
      "href",
      "/studio",
    );
    expect(screen.getByAltText("Orbit AI localized creative proposal")).toHaveAttribute(
      "src",
      expect.stringContaining("composed-china-to-uk.png"),
    );
  });
});
