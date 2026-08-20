import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { loadFixture } from "../fixtures/fixture-loader";

import { DraftEvidence } from "./draft-evidence";

describe("DraftEvidence", () => {
  it.each([
    ["china-to-uk", "Turn approved notes into clear task summaries", "ZEU-S1"],
    ["uk-to-china", "把已批准笔记整理成清晰任务摘要", "EZC-S1"],
  ] as const)("shows factual bilingual evidence for %s", (fixtureId, headline, ruleId) => {
    const fixture = loadFixture(fixtureId);
    render(<DraftEvidence draft={fixture.draft} disclosure={fixture.disclosure} />);

    expect(
      screen.getByRole("heading", { level: 2, name: "Creative brief / 创意简报" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: headline })).toBeInTheDocument();
    expect(screen.getByText(ruleId)).toBeInTheDocument();
    expect(screen.getByText("Start a fixture demo")).toBeInTheDocument();
    expect(screen.getByText("Fixture Demo / 非实时模型")).toBeInTheDocument();
    expect(screen.getByText(/Human review required/i)).toBeInTheDocument();
    expect(screen.getByText(/not cultural, legal, or performance validation/i)).toBeInTheDocument();
  });
});
