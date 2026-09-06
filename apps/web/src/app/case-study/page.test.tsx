import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import CaseStudy from "./page";

describe("CultureShift case study introduction", () => {
  it("frames the problem and compares both workflow models", () => {
    render(<CaseStudy />);

    expect(screen.getByRole("heading", { level: 1, name: "CultureShift" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Localization" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Brand Truth" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "AI Uncertainty" })).toBeInTheDocument();
    expect(screen.getByText("Traditional prompt-to-output")).toBeInTheDocument();
    expect(screen.getByText("CultureShift constrained workflow")).toBeInTheDocument();
    expect(screen.getAllByText("CulturalHypothesis")).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "Brand Lock" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Human-in-the-Loop" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "From authorized input to accountable decision." })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "System Architecture" })).toBeInTheDocument();
    expect(screen.getByText("Next.js Studio")).toBeInTheDocument();
    expect(screen.getByText("FastAPI application layer")).toBeInTheDocument();
    expect(screen.getByText("SQLite persistence")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open the Studio" })).toHaveAttribute(
      "href",
      "/studio",
    );
  });
});
