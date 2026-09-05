import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type {
  AnalysisCompleted,
  AssetUploaded,
  BrandLockConfirmed,
  CompositionGenerated,
  CritiqueCompleted,
  DraftGenerated,
  RevisionCompleted,
  RunCreated,
} from "../../generated/contracts";
import { loadFixture } from "../../fixtures/fixture-loader";
import { StudioApiError, type StudioApiClient } from "../../studio/studio-api";

import { StudioClient } from "./studio-client";

function fakeApi(): StudioApiClient {
  return {
    uploadAsset: vi.fn(),
    createRun: vi.fn(),
    analyzeRun: vi.fn(),
    confirmBrandLock: vi.fn(),
    generateDraft: vi.fn(),
    generateComposition: vi.fn(),
    runCritic: vi.fn(),
    submitFeedback: vi.fn(),
    retryRevision: vi.fn(),
    exportComposition: vi.fn(),
    deleteAsset: vi.fn(),
  };
}

const fixture = loadFixture("china-to-uk");
const timestamp = "2026-08-27T08:00:00Z";
const uploaded: AssetUploaded = {
  asset: {
    ...fixture.request.source_asset,
    media_type: "image/png",
    provenance_ref: "fixture://day16/source",
    rights_ref: "rights://authorized/day16",
  },
  created_at: timestamp,
  delete_capability_token: "delete-secret",
  size_bytes: 7,
};
const run: RunCreated = {
  run_id: "d1611111-1111-4111-8111-111111111111",
  capability_token: "run-secret",
  created_at: timestamp,
  status: "pending",
};
const analysis: AnalysisCompleted = {
  run_id: run.run_id,
  status: "awaiting_brand_lock",
  repair_attempted: false,
  completed_at: timestamp,
  analysis: {
    source_asset: uploaded.asset,
    detected_locale: fixture.source_locale,
    brand_lock: fixture.preview.brand_lock,
    hypotheses: [...fixture.preview.hypotheses],
    warnings: [...fixture.preview.warnings],
  },
};
const confirmation: BrandLockConfirmed = {
  run_id: run.run_id,
  status: "in_progress",
  brand_lock: fixture.preview.brand_lock,
  confirmed_at: timestamp,
};
const draft: DraftGenerated = {
  run_id: run.run_id,
  status: "in_progress",
  generated_at: timestamp,
  brief: fixture.draft.brief,
  copy: fixture.draft.copy,
  rule_ids: fixture.draft.rule_ids as DraftGenerated["rule_ids"],
};
const composition: CompositionGenerated = {
  run_id: run.run_id,
  status: "in_progress",
  artifact_id: "d1622222-2222-4222-8222-222222222222",
  generated_at: timestamp,
  execution_mode: "fixture",
  width: fixture.composition.width,
  height: fixture.composition.height,
  media_type: "image/png",
  rendered_sha256: fixture.composition.rendered_sha256,
  layers: [...fixture.composition.layers] as CompositionGenerated["layers"],
  disclosure: fixture.disclosure,
};
const critique: CritiqueCompleted = {
  run_id: run.run_id,
  status: "ready",
  initial_generation_count: 1,
  human_revision_count: 0,
  technical_attempt_count: 0,
  reviewed_at: timestamp,
  critique: {
    status: "pass",
    brand_lock_preserved: true,
    requires_human_review: true,
    issues: [],
    warnings: ["HUMAN_REVIEW_REQUIRED"],
    reviewed_at: timestamp,
  },
};
const revision: RevisionCompleted = {
  run_id: run.run_id,
  status: "ready",
  result_version: 2,
  initial_generation_count: 1,
  human_revision_count: 1,
  technical_attempt_count: 0,
  revised_at: timestamp,
  brief: draft.brief,
  copy: { ...draft.copy, headline: "Clear task summaries" },
  previous_composition: composition,
  composition: {
    ...composition,
    artifact_id: "d1633333-3333-4333-8333-333333333333",
    rendered_sha256: "a".repeat(64),
  },
  critique: critique.critique,
};

function happyApi(): StudioApiClient {
  return {
    uploadAsset: vi.fn().mockResolvedValue(uploaded),
    createRun: vi.fn().mockResolvedValue(run),
    analyzeRun: vi.fn().mockResolvedValue(analysis),
    confirmBrandLock: vi.fn().mockResolvedValue(confirmation),
    generateDraft: vi.fn().mockResolvedValue(draft),
    generateComposition: vi.fn().mockResolvedValue(composition),
    runCritic: vi.fn().mockResolvedValue(critique),
    submitFeedback: vi.fn().mockResolvedValue(revision),
    retryRevision: vi.fn(),
    exportComposition: vi.fn().mockResolvedValue(new Blob(["png"], { type: "image/png" })),
    deleteAsset: vi.fn(),
  };
}

async function reachReadyVersionOne() {
  selectAuthorizedPng();
  fireEvent.click(screen.getByRole("button", { name: "Upload and start" }));
  await screen.findByRole("heading", { name: "Confirm Brand Lock" });
  fireEvent.click(screen.getByRole("checkbox", { name: /become immutable/i }));
  fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));
  await screen.findByText(/Brand Lock confirmed and immutable/);
  fireEvent.click(screen.getByRole("button", { name: "Generate fixture proposal" }));
  await screen.findByRole("heading", { name: "Version 1" });
}

function selectAuthorizedPng() {
  fireEvent.change(screen.getByLabelText("Provenance reference"), {
    target: { value: "fixture://day16/source" },
  });
  fireEvent.change(screen.getByLabelText("Rights reference"), {
    target: { value: "rights://authorized/day16" },
  });
  fireEvent.click(
    screen.getByRole("checkbox", { name: /authority to process/i }),
  );
  fireEvent.change(screen.getByLabelText("Source ad"), {
    target: {
      files: [new File(["fixture"], "source.png", { type: "image/png" })],
    },
  });
}

describe("StudioClient", () => {
  it("requires an authorized supported source before upload", () => {
    render(<StudioClient api={fakeApi()} />);

    expect(screen.getByRole("heading", { name: "Connected fixture Studio" })).toBeVisible();
    expect(screen.getByRole("radio", { name: "China to UK" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "UK to China" })).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Upload and start" })).toBeDisabled();

    selectAuthorizedPng();

    expect(screen.getByRole("button", { name: "Upload and start" })).toBeEnabled();
  });

  it("orients a first-time user and exposes a non-navigable accessible progress list", () => {
    render(<StudioClient api={fakeApi()} />);
    expect(screen.getByText(/This is a fixture demonstration/i)).toBeVisible();
    expect(screen.getByText(/no live AI provider/i)).toBeVisible();
    expect(screen.getByText(/hypotheses requiring human review/i)).toBeVisible();
    const progress = screen.getByRole("list", { name: "Studio progress" });
    expect(progress).toHaveTextContent("Configure direction");
    expect(progress).toHaveTextContent("Export or delete");
    expect(progress.querySelector('[aria-current="step"]')).not.toBeNull();
  });

  it("rejects unsupported or oversized files without exposing their names", () => {
    render(<StudioClient api={fakeApi()} />);

    fireEvent.change(screen.getByLabelText("Source ad"), {
      target: {
        files: [new File(["private"], "private-script.svg", { type: "image/svg+xml" })],
      },
    });
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Choose a PNG, JPEG, or WebP source no larger than 10 MiB.",
    );
    expect(screen.getByRole("alert")).not.toHaveTextContent("private-script.svg");
  });

  it("runs the authorized source through Brand Lock and ready version one", async () => {
    const api = happyApi();
    render(<StudioClient api={api} />);
    selectAuthorizedPng();

    fireEvent.click(screen.getByRole("button", { name: "Upload and start" }));

    expect(
      await screen.findByRole("heading", { name: "Confirm Brand Lock" }),
    ).toBeVisible();
    expect(api.createRun).toHaveBeenCalledWith({
      ...fixture.request,
      source_asset: uploaded.asset,
    });
    expect(api.analyzeRun).toHaveBeenCalledWith(run.run_id, run.capability_token);

    fireEvent.click(screen.getByRole("checkbox", { name: /become immutable/i }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));
    expect(
      await screen.findByText(/Brand Lock confirmed and immutable/),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Generate fixture proposal" }),
    ).toBeEnabled();

    fireEvent.click(
      screen.getByRole("button", { name: "Generate fixture proposal" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Version 1" }),
    ).toBeVisible();
    expect(screen.getByText("Fixture Demo / 非实时模型")).toBeVisible();
    expect(screen.getByText("Human review required")).toBeVisible();
    expect(
      screen.getByRole("heading", { name: fixture.draft.copy.headline }),
    ).toBeVisible();
    expect(
      screen.getByText(fixture.preview.hypotheses[0].evidence_refs[0]),
    ).toBeVisible();
    expect(screen.getByText(fixture.preview.warnings[0])).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Export version 1 PNG" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Export version 1 JSON" }),
    ).toBeVisible();
    await waitFor(() =>
      expect(api.exportComposition).toHaveBeenCalledWith(
        run.run_id,
        run.capability_token,
        1,
        "png",
      ),
    );
    expect(document.body).not.toHaveTextContent(run.capability_token);
    expect(document.body).not.toHaveTextContent(uploaded.delete_capability_token);
  });

  it("connects the UK-to-China fixture through the same ordered version-one contract", async () => {
    const ukFixture = loadFixture("uk-to-china");
    const ukUpload: AssetUploaded = {
      ...uploaded,
      asset: { ...uploaded.asset, asset_id: ukFixture.request.source_asset.asset_id },
    };
    const api = happyApi();
    vi.mocked(api.uploadAsset).mockResolvedValue(ukUpload);
    vi.mocked(api.analyzeRun).mockResolvedValue({
      ...analysis,
      analysis: {
        ...analysis.analysis,
        source_asset: ukUpload.asset,
        detected_locale: ukFixture.source_locale,
        brand_lock: ukFixture.preview.brand_lock,
        hypotheses: [...ukFixture.preview.hypotheses],
      },
    });
    vi.mocked(api.generateDraft).mockResolvedValue({
      ...draft,
      brief: ukFixture.draft.brief,
      copy: ukFixture.draft.copy,
      rule_ids: ukFixture.draft.rule_ids as DraftGenerated["rule_ids"],
    });
    render(<StudioClient api={api} />);
    fireEvent.click(screen.getByRole("radio", { name: "UK to China" }));

    await reachReadyVersionOne();

    expect(api.createRun).toHaveBeenCalledWith({
      ...ukFixture.request,
      source_asset: ukUpload.asset,
    });
    const ordered = [
      api.uploadAsset,
      api.createRun,
      api.analyzeRun,
      api.confirmBrandLock,
      api.generateDraft,
      api.generateComposition,
      api.runCritic,
      api.exportComposition,
    ].map((mock) => vi.mocked(mock).mock.invocationCallOrder[0]);
    expect(ordered).toEqual([...ordered].sort((left, right) => left - right));
    expect(screen.getByText("Detected locale: en-GB")).toBeVisible();
  });

  it("never presents a Critic rejection as a ready result", async () => {
    const api = happyApi();
    vi.mocked(api.runCritic).mockResolvedValue({ ...critique, status: "failed_final" });
    render(<StudioClient api={api} />);
    selectAuthorizedPng();
    fireEvent.click(screen.getByRole("button", { name: "Upload and start" }));
    await screen.findByRole("heading", { name: "Confirm Brand Lock" });
    fireEvent.click(screen.getByRole("checkbox", { name: /become immutable/i }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm Brand Lock" }));
    await screen.findByText(/Brand Lock confirmed and immutable/);
    fireEvent.click(screen.getByRole("button", { name: "Generate fixture proposal" }));

    expect(await screen.findByText("Current phase: final failure")).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Version 1" })).not.toBeInTheDocument();
    expect(api.exportComposition).not.toHaveBeenCalled();
  });

  it("offers one bounded retry only after a retryable revision failure", async () => {
    const api = happyApi();
    vi.mocked(api.submitFeedback).mockRejectedValue(
      new StudioApiError(503, "revision_failed"),
    );
    vi.mocked(api.retryRevision).mockResolvedValue(revision);
    render(<StudioClient api={api} />);
    await reachReadyVersionOne();
    fireEvent.click(screen.getByRole("checkbox", { name: "Shorten headline" }));
    fireEvent.change(screen.getByLabelText("Feedback context"), {
      target: { value: "Hard to scan." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create version 2" }));

    const retry = await screen.findByRole("button", { name: "Retry version 2" });
    fireEvent.click(retry);

    expect(
      await screen.findByRole("heading", { name: "Compare versions" }),
    ).toBeVisible();
    expect(api.retryRevision).toHaveBeenCalledWith(
      run.run_id,
      run.capability_token,
      { run_id: run.run_id, reason_category: "generation" },
      expect.any(String),
    );
    expect(api.exportComposition).toHaveBeenCalledWith(
      run.run_id,
      run.capability_token,
      2,
      "png",
    );
  });

  it("creates only version two, exports it, and deletes the exact source", async () => {
    const api = happyApi();
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    render(<StudioClient api={api} />);
    await reachReadyVersionOne();

    fireEvent.click(screen.getByRole("checkbox", { name: "Shorten headline" }));
    fireEvent.change(screen.getByLabelText("Feedback context"), {
      target: { value: "Headline is difficult to scan." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create version 2" }));

    expect(
      await screen.findByRole("heading", { name: "Compare versions" }),
    ).toBeVisible();
    expect(screen.getByRole("heading", { name: "Version 1" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Version 2" })).toBeVisible();
    expect(screen.queryByText("Version 3")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Export version 2 PNG" }));
    await waitFor(() =>
      expect(api.exportComposition).toHaveBeenCalledWith(
        run.run_id,
        run.capability_token,
        2,
        "png",
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Review source deletion" }));
    expect(screen.getByRole("group", { name: "Confirm source deletion" })).toHaveTextContent(
      "downloaded to your device",
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancel deletion" }));
    expect(api.deleteAsset).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Review source deletion" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm delete source and reset" }));
    await waitFor(() =>
      expect(api.deleteAsset).toHaveBeenCalledWith(
        uploaded.asset.asset_id,
        uploaded.delete_capability_token,
      ),
    );
    expect(await screen.findByText(/Only the uploaded source asset was deleted/i)).toBeVisible();
    expect(screen.getByRole("button", { name: "Upload and start" })).toBeDisabled();
    click.mockRestore();
  });
});
