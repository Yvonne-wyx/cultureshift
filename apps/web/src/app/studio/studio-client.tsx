"use client";
/* eslint-disable @next/next/no-img-element */

import { useEffect, useReducer, useRef, useState } from "react";

import { BrandLockForm } from "../../components/brand-lock-form";
import { DraftEvidence } from "../../components/draft-evidence";
import type { FeedbackRequest, RevisionChange } from "../../generated/contracts";
import { loadFixture } from "../../fixtures/fixture-loader";
import type { StudioApiClient } from "../../studio/studio-api";
import { createStudioApiClient, StudioApiError } from "../../studio/studio-api";
import {
  canGenerate,
  canDelete,
  canRetry,
  canSubmitRevision,
  canUpload,
  initialStudioState,
  studioReducer,
} from "../../studio/studio-state";

import styles from "./studio.module.css";

const MAX_SOURCE_BYTES = 10 * 1024 * 1024;
const SUPPORTED_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);
const INVALID_FILE_MESSAGE =
  "Choose a PNG, JPEG, or WebP source no larger than 10 MiB.";

export interface StudioClientProps {
  api?: StudioApiClient;
}

export function StudioClient({ api = createStudioApiClient() }: StudioClientProps) {
  const [state, dispatch] = useReducer(
    studioReducer,
    initialStudioState("china-to-uk"),
  );
  const [source, setSource] = useState<File>();
  const [provenanceRef, setProvenanceRef] = useState("");
  const [rightsRef, setRightsRef] = useState("");
  const [hasAuthority, setHasAuthority] = useState(false);
  const [fileError, setFileError] = useState<string>();
  const [operationError, setOperationError] = useState<string>();
  const [completionMessage, setCompletionMessage] = useState<string>();
  const [sourceUrl, setSourceUrl] = useState<string>();
  const [versionOneUrl, setVersionOneUrl] = useState<string>();
  const [versionTwoUrl, setVersionTwoUrl] = useState<string>();
  const [shortenHeadline, setShortenHeadline] = useState(false);
  const [shortenBody, setShortenBody] = useState(false);
  const [feedback, setFeedback] = useState("");
  const feedbackKey = useRef<string | undefined>(undefined);
  const retryKey = useRef<string | undefined>(undefined);
  const revisionRequest = useRef<FeedbackRequest | undefined>(undefined);
  const fixture = loadFixture(state.fixtureId);

  useEffect(() => () => {
    if (sourceUrl) URL.revokeObjectURL(sourceUrl);
  }, [sourceUrl]);
  useEffect(() => () => {
    if (versionOneUrl) URL.revokeObjectURL(versionOneUrl);
  }, [versionOneUrl]);
  useEffect(() => () => {
    if (versionTwoUrl) URL.revokeObjectURL(versionTwoUrl);
  }, [versionTwoUrl]);

  function fail(error: unknown) {
    const code = error instanceof StudioApiError ? error.code : "service_unavailable";
    dispatch({ type: "operation_failed", code });
    setOperationError(`Studio operation failed (${code}). Start a clean run if needed.`);
  }

  async function startRun() {
    if (!readyToUpload || !source) return;
    setOperationError(undefined);
    dispatch({ type: "upload_started" });
    try {
      const upload = await api.uploadAsset(source, { provenanceRef, rightsRef });
      dispatch({ type: "upload_succeeded", result: upload });
      const created = await api.createRun({
        ...fixture.request,
        source_asset: upload.asset,
      });
      dispatch({ type: "run_created", result: created });
      const analyzed = await api.analyzeRun(
        created.run_id,
        created.capability_token,
      );
      dispatch({ type: "analysis_succeeded", result: analyzed });
    } catch (error) {
      fail(error);
    }
  }

  function makeObjectUrl(blob: Blob): string | undefined {
    return typeof URL.createObjectURL === "function"
      ? URL.createObjectURL(blob)
      : undefined;
  }

  async function generateVersionOne() {
    if (!canGenerate(state) || !state.run) return;
    setOperationError(undefined);
    dispatch({ type: "generation_started" });
    try {
      const generatedDraft = await api.generateDraft(
        state.run.run_id,
        state.run.capability_token,
      );
      dispatch({ type: "draft_succeeded", result: generatedDraft });
      const generatedComposition = await api.generateComposition(
        state.run.run_id,
        state.run.capability_token,
      );
      dispatch({ type: "composition_succeeded", result: generatedComposition });
      const reviewed = await api.runCritic(
        state.run.run_id,
        state.run.capability_token,
      );
      dispatch({ type: "critic_succeeded", result: reviewed });
      if (reviewed.status === "ready") {
        const blob = await api.exportComposition(
          state.run.run_id,
          state.run.capability_token,
          1,
          "png",
        );
        setVersionOneUrl(makeObjectUrl(blob));
      }
    } catch (error) {
      fail(error);
    }
  }

  async function createVersionTwo() {
    if (!canSubmitRevision(state) || !state.run) return;
    const requestedChanges: RevisionChange[] = [];
    if (shortenHeadline) requestedChanges.push("shorten_headline");
    if (shortenBody) requestedChanges.push("shorten_body");
    if (requestedChanges.length === 0 || feedback.trim() === "") return;

    const request: FeedbackRequest = {
      run_id: state.run.run_id,
      feedback: feedback.trim(),
      requested_changes: requestedChanges as FeedbackRequest["requested_changes"],
      submitted_at: new Date().toISOString(),
    };
    feedbackKey.current ??= crypto.randomUUID();
    revisionRequest.current = request;
    dispatch({ type: "revision_started" });
    setOperationError(undefined);
    try {
      const result = await api.submitFeedback(
        state.run.run_id,
        state.run.capability_token,
        request,
        feedbackKey.current,
      );
      dispatch({ type: "revision_succeeded", result });
      const blob = await api.exportComposition(
        state.run.run_id,
        state.run.capability_token,
        2,
        "png",
      );
      setVersionTwoUrl(makeObjectUrl(blob));
    } catch (error) {
      fail(error);
    }
  }

  async function retryVersionTwo() {
    if (!canRetry(state) || !state.run || !revisionRequest.current) return;
    retryKey.current ??= crypto.randomUUID();
    dispatch({ type: "retry_started" });
    try {
      const result = await api.retryRevision(
        state.run.run_id,
        state.run.capability_token,
        { run_id: state.run.run_id, reason_category: "generation" },
        retryKey.current,
      );
      dispatch({ type: "revision_succeeded", result });
      const blob = await api.exportComposition(
        state.run.run_id,
        state.run.capability_token,
        2,
        "png",
      );
      setVersionTwoUrl(makeObjectUrl(blob));
    } catch (error) {
      fail(error);
    }
  }

  async function downloadVersion(version: 1 | 2, format: "png" | "json") {
    if (!state.run) return;
    try {
      const blob = await api.exportComposition(
        state.run.run_id,
        state.run.capability_token,
        version,
        format,
      );
      const url = makeObjectUrl(blob);
      if (!url) return;
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `cultureshift-version-${version}.${format}`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      fail(error);
    }
  }

  async function deleteSource() {
    if (!canDelete(state) || !state.upload) return;
    dispatch({ type: "delete_started" });
    setOperationError(undefined);
    try {
      await api.deleteAsset(
        state.upload.asset.asset_id,
        state.upload.delete_capability_token,
      );
      for (const url of [sourceUrl, versionOneUrl, versionTwoUrl]) {
        if (url) URL.revokeObjectURL(url);
      }
      setSource(undefined);
      setSourceUrl(undefined);
      setVersionOneUrl(undefined);
      setVersionTwoUrl(undefined);
      setProvenanceRef("");
      setRightsRef("");
      setHasAuthority(false);
      setShortenHeadline(false);
      setShortenBody(false);
      setFeedback("");
      feedbackKey.current = undefined;
      retryKey.current = undefined;
      revisionRequest.current = undefined;
      dispatch({ type: "delete_succeeded" });
      setCompletionMessage(
        "Only the uploaded source asset was deleted; the Studio session was reset.",
      );
    } catch (error) {
      fail(error);
    }
  }

  const readyToUpload =
    canUpload(state) &&
    source !== undefined &&
    provenanceRef.trim() !== "" &&
    rightsRef.trim() !== "" &&
    hasAuthority;

  return (
    <main className={styles.shell}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>Day 16 · fixture-only integration</p>
        <h1>Connected fixture Studio</h1>
        <p>
          Run one authorized source through the existing deterministic workflow.
          Nothing is published automatically.
        </p>
      </header>

      <section className={styles.panel} aria-labelledby="configure-studio">
        <h2 id="configure-studio">Configure a fixture run</h2>
        <fieldset className={styles.fields}>
          <legend>Direction</legend>
          <label>
            <input
              type="radio"
              name="direction"
              checked={state.fixtureId === "china-to-uk"}
              onChange={() =>
                dispatch({ type: "fixture_selected", fixtureId: "china-to-uk" })
              }
            />
            China to UK
          </label>
          <label>
            <input
              type="radio"
              name="direction"
              checked={state.fixtureId === "uk-to-china"}
              onChange={() =>
                dispatch({ type: "fixture_selected", fixtureId: "uk-to-china" })
              }
            />
            UK to China
          </label>
        </fieldset>

        <div className={styles.fields}>
          <label>
            Source ad
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => {
                const next = event.target.files?.[0];
                if (
                  !next ||
                  !SUPPORTED_TYPES.has(next.type) ||
                  next.size > MAX_SOURCE_BYTES
                ) {
                  setSource(undefined);
                  setFileError(INVALID_FILE_MESSAGE);
                  return;
                }
                setSource(next);
                if (sourceUrl) URL.revokeObjectURL(sourceUrl);
                setSourceUrl(makeObjectUrl(next));
                setFileError(undefined);
              }}
            />
          </label>
          {fileError ? <p role="alert">{fileError}</p> : null}
          <label>
            Provenance reference
            <input
              value={provenanceRef}
              onChange={(event) => setProvenanceRef(event.target.value)}
            />
          </label>
          <label>
            Rights reference
            <input
              value={rightsRef}
              onChange={(event) => setRightsRef(event.target.value)}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={hasAuthority}
              onChange={(event) => setHasAuthority(event.target.checked)}
            />
            I have authority to process this source.
          </label>
          <button type="button" disabled={!readyToUpload} onClick={startRun}>
            Upload and start
          </button>
        </div>
      </section>

      {state.phase !== "configure" ? (
        <p className={styles.status} role="status">
          Current phase: {state.phase.replaceAll("_", " ")}
        </p>
      ) : null}
      {operationError ? <p role="alert">{operationError}</p> : null}
      {completionMessage ? <p role="status">{completionMessage}</p> : null}

      {state.analysis && state.run ? (
        <>
          <section className={styles.panel} aria-label="Analysis evidence">
            <h2>Analysis evidence</h2>
            <p>Detected locale: {state.analysis.analysis.detected_locale}</p>
            <p>Pending hypotheses remain subject to human review.</p>
            <h3>Warnings</h3>
            <ul>
              {(state.analysis.analysis.warnings ?? []).map((warning) => (
                <li key={warning}><code>{warning}</code></li>
              ))}
            </ul>
            <h3>Evidence references</h3>
            <ul>
              {(state.analysis.analysis.hypotheses ?? []).flatMap((hypothesis) =>
                hypothesis.evidence_refs.map((reference) => (
                  <li key={`${hypothesis.hypothesis_id}-${reference}`}>
                    <code>{reference}</code>
                  </li>
                )),
              )}
            </ul>
          </section>
          <BrandLockForm
            initialBrandLock={state.analysis.analysis.brand_lock}
            directionLabel={state.fixtureId === "china-to-uk" ? "China to UK" : "UK to China"}
            logoAssetPath={fixture.preview.logo_asset_path}
            productUiAssetPath={fixture.preview.product_ui_asset_path}
            layoutPreview={fixture.preview.localized_copy}
            confirmBrandLock={async (brandLock) => {
              const confirmed = await api.confirmBrandLock(
                state.run!.run_id,
                state.run!.capability_token,
                brandLock,
              );
              dispatch({ type: "brand_lock_confirmed", result: confirmed });
              return confirmed;
            }}
          />
        </>
      ) : null}

      {canGenerate(state) ? (
        <button className={styles.primaryAction} type="button" onClick={generateVersionOne}>
          Generate fixture proposal
        </button>
      ) : null}

      {state.phase === "ready_v1" && state.draft && state.composition && state.critique ? (
        <section className={styles.results} aria-labelledby="version-one-heading">
          <h2 id="version-one-heading">Version 1</h2>
          {sourceUrl ? (
            <img src={sourceUrl} alt="Authorized source ad preview" />
          ) : null}
          {versionOneUrl ? (
            // The authenticated Blob URL contains no capability or API address.
            <img src={versionOneUrl} alt="Generated version 1 fixture composition" />
          ) : null}
          <DraftEvidence
            draft={{
              brief: {
                ...state.draft.brief,
                hypotheses: state.draft.brief.hypotheses ?? [],
              },
              copy: state.draft.copy,
              rule_ids: state.draft.rule_ids,
              prompt_summary: fixture.draft.prompt_summary,
            }}
            disclosure={fixture.disclosure}
          />
          <dl>
            <div><dt>Critic</dt><dd>{state.critique.critique.status}</dd></div>
            <div><dt>Output SHA-256</dt><dd><code>{state.composition.rendered_sha256}</code></dd></div>
          </dl>
          <div className={styles.actions}>
            <button type="button" onClick={() => downloadVersion(1, "png")}>Export version 1 PNG</button>
            <button type="button" onClick={() => downloadVersion(1, "json")}>Export version 1 JSON</button>
          </div>
          <fieldset className={styles.feedback}>
            <legend>One structured revision</legend>
            <label><input type="checkbox" checked={shortenHeadline} onChange={(event) => setShortenHeadline(event.target.checked)} /> Shorten headline</label>
            <label><input type="checkbox" checked={shortenBody} onChange={(event) => setShortenBody(event.target.checked)} /> Shorten body</label>
            <label>
              Feedback context
              <textarea maxLength={500} value={feedback} onChange={(event) => setFeedback(event.target.value)} />
            </label>
            <button
              type="button"
              disabled={(!shortenHeadline && !shortenBody) || feedback.trim() === ""}
              onClick={createVersionTwo}
            >
              Create version 2
            </button>
          </fieldset>
        </section>
      ) : null}

      {state.phase === "ready_v2" && state.revision ? (
        <section className={styles.results} aria-labelledby="compare-heading">
          <h2 id="compare-heading">Compare versions</h2>
          <div className={styles.comparison}>
            <article><h3>Version 1</h3><code>{state.revision.previous_composition.rendered_sha256}</code>{versionOneUrl ? <img src={versionOneUrl} alt="Version 1 composition" /> : null}</article>
            <article><h3>Version 2</h3><code>{state.revision.composition.rendered_sha256}</code>{versionTwoUrl ? <img src={versionTwoUrl} alt="Version 2 composition" /> : null}</article>
          </div>
          <p>Human revision count: {state.revision.human_revision_count}</p>
          <p>Critic: {state.revision.critique.status}; human review required.</p>
          <button type="button" onClick={() => downloadVersion(1, "png")}>Export version 1 PNG</button>
          <button type="button" onClick={() => downloadVersion(1, "json")}>Export version 1 JSON</button>
          <button type="button" onClick={() => downloadVersion(2, "png")}>Export version 2 PNG</button>
          <button type="button" onClick={() => downloadVersion(2, "json")}>Export version 2 JSON</button>
        </section>
      ) : null}

      {canRetry(state) ? <button type="button" onClick={retryVersionTwo}>Retry version 2</button> : null}
      {canDelete(state) ? (
        <section className={styles.dangerZone}>
          <p>This deletes only the uploaded source asset, not Run metadata or generated records.</p>
          <button type="button" onClick={deleteSource}>Delete uploaded source and reset</button>
        </section>
      ) : null}
    </main>
  );
}
