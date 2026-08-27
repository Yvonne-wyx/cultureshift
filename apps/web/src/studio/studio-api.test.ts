import { describe, expect, it, vi } from "vitest";

import { loadFixture } from "../fixtures/fixture-loader";
import type { AssetUploaded, FeedbackRequest, RetryRequest } from "../generated/contracts";

import { createStudioApiClient, StudioApiError } from "./studio-api";

const runId = "11111111-1111-4111-8111-111111111111";
const runToken = "run-capability-private-value";
const deleteToken = "delete-capability-private-value";
const fixture = loadFixture("china-to-uk");

const uploaded: AssetUploaded = {
  asset: {
    asset_id: "22222222-2222-4222-8222-222222222222",
    kind: "source_ad",
    media_type: "image/png",
    sha256: "a".repeat(64),
    provenance_ref: "fixture://day16/source",
    rights_ref: "rights://authorized/day16",
    expires_at: "2026-08-28T00:00:00Z",
  },
  size_bytes: 12,
  created_at: "2026-08-27T00:00:00Z",
  delete_capability_token: deleteToken,
};

function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("StudioApiClient", () => {
  it("uploads raw bytes with public metadata and no capability URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(uploaded, 201));
    const api = createStudioApiClient("http://127.0.0.1:8000", fetchMock);
    const file = new File(["fixture-png"], "source.png", { type: "image/png" });

    await expect(
      api.uploadAsset(file, {
        provenanceRef: "fixture://day16/source",
        rightsRef: "rights://authorized/day16",
      }),
    ).resolves.toEqual(uploaded);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8000/api/v1/assets");
    expect(url).not.toMatch(/capability|token/i);
    expect(init).toMatchObject({ method: "POST", body: file });
    expect(init.headers).toEqual({
      "Content-Type": "image/png",
      "X-Provenance-Ref": "fixture://day16/source",
      "X-Rights-Ref": "rights://authorized/day16",
    });
  });

  it("constructs every Run mutation with exact authorization and idempotency", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: { code: "invalid_run_state" } }, 409));
    const api = createStudioApiClient("http://127.0.0.1:8000", fetchMock);
    const feedback: FeedbackRequest = {
      run_id: runId,
      feedback: "Shorten without changing protected values.",
      requested_changes: ["shorten_headline"],
      submitted_at: "2026-08-27T00:00:00Z",
    };
    const retry: RetryRequest = { run_id: runId, reason_category: "generation" };

    const calls = [
      () => api.analyzeRun(runId, runToken),
      () => api.confirmBrandLock(runId, runToken, fixture.preview.brand_lock),
      () => api.generateDraft(runId, runToken),
      () => api.generateComposition(runId, runToken),
      () => api.runCritic(runId, runToken),
      () => api.submitFeedback(runId, runToken, feedback, "revision_key_1234"),
      () => api.retryRevision(runId, runToken, retry, "retry_key_123456"),
    ];
    for (const call of calls) await call().catch(() => undefined);

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `http://127.0.0.1:8000/api/v1/runs/${runId}/analyze`,
      `http://127.0.0.1:8000/api/v1/runs/${runId}/brand-lock/confirm`,
      `http://127.0.0.1:8000/api/v1/runs/${runId}/draft`,
      `http://127.0.0.1:8000/api/v1/runs/${runId}/composition`,
      `http://127.0.0.1:8000/api/v1/runs/${runId}/critic`,
      `http://127.0.0.1:8000/api/v1/runs/${runId}/feedback`,
      `http://127.0.0.1:8000/api/v1/runs/${runId}/retry`,
    ]);
    for (const [, init] of fetchMock.mock.calls) {
      expect(init.headers.Authorization).toBe(`Bearer ${runToken}`);
    }
    expect(fetchMock.mock.calls[0][1].body).toBeUndefined();
    expect(fetchMock.mock.calls[1][1].body).toBe(
      JSON.stringify({ brand_lock: fixture.preview.brand_lock }),
    );
    expect(fetchMock.mock.calls[5][1].headers["Idempotency-Key"]).toBe(
      "revision_key_1234",
    );
    expect(fetchMock.mock.calls[5][1].body).toBe(JSON.stringify(feedback));
    expect(fetchMock.mock.calls[6][1].headers["Idempotency-Key"]).toBe(
      "retry_key_123456",
    );
    expect(fetchMock.mock.calls[6][1].body).toBe(JSON.stringify(retry));
  });

  it("fetches the selected export as a validated binary without token URLs", async () => {
    const png = new Blob(["verified-png"], { type: "image/png" });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(png, { status: 200, headers: { "Content-Type": "image/png" } }),
    );
    const api = createStudioApiClient("http://127.0.0.1:8000", fetchMock);

    const result = await api.exportComposition(runId, runToken, 2, "png");

    expect(result.type).toBe("image/png");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(
      `http://127.0.0.1:8000/api/v1/runs/${runId}/composition.png?result_version=2`,
    );
    expect(url).not.toContain(runToken);
    expect(init.headers).toEqual({ Authorization: `Bearer ${runToken}` });
  });

  it("deletes only the addressed asset with its delete capability", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    const api = createStudioApiClient("http://127.0.0.1:8000", fetchMock);

    await expect(
      api.deleteAsset(uploaded.asset.asset_id, deleteToken),
    ).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith(
      `http://127.0.0.1:8000/api/v1/assets/${uploaded.asset.asset_id}`,
      { method: "DELETE", headers: { Authorization: `Bearer ${deleteToken}` } },
    );
  });

  it("keeps only bounded error codes and hides malformed private responses", async () => {
    const bounded = createStudioApiClient(
      undefined,
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: { code: "idempotency_conflict" } }, 409),
      ),
    );
    const malformed = createStudioApiClient(
      undefined,
      vi.fn().mockResolvedValue(new Response("private traceback", { status: 500 })),
    );

    const known = await bounded.analyzeRun(runId, runToken).catch((error) => error);
    const unknown = await malformed.analyzeRun(runId, runToken).catch((error) => error);

    expect(known).toEqual(
      expect.objectContaining({ status: 409, code: "idempotency_conflict" }),
    );
    expect(unknown).toEqual(
      expect.objectContaining({ status: 500, code: "service_unavailable" }),
    );
    expect(known).toBeInstanceOf(StudioApiError);
    expect(String(known) + String(unknown)).not.toMatch(
      /private traceback|run-capability-private-value/,
    );
  });
});
