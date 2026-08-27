import type {
  AnalysisCompleted,
  AssetUploaded,
  BrandLock,
  BrandLockConfirmed,
  CompositionGenerated,
  CritiqueCompleted,
  DraftGenerated,
  FeedbackRequest,
  RetryRequest,
  RevisionCompleted,
  RunCreate,
  RunCreated,
} from "../generated/contracts";

export interface UploadMetadata {
  provenanceRef: string;
  rightsRef: string;
}

export type StudioErrorCode =
  | "validation_failed"
  | "asset_empty"
  | "unsupported_asset_type"
  | "asset_type_mismatch"
  | "asset_too_large"
  | "invalid_asset_metadata"
  | "upload_rate_limited"
  | "asset_lifecycle_closed"
  | "invalid_capability"
  | "capability_subject_mismatch"
  | "run_not_found"
  | "invalid_run_state"
  | "brand_lock_immutable"
  | "brand_lock_unconfirmed"
  | "locked_field_changed"
  | "benefit_order_invalid"
  | "localizable_fields_invalid"
  | "invalid_analysis_input"
  | "unsupported_analysis_scope"
  | "provider_failed"
  | "provider_output_invalid"
  | "instruction_like_content"
  | "prohibited_content"
  | "unsafe_hypothesis"
  | "draft_output_invalid"
  | "composition_output_invalid"
  | "critic_failed"
  | "operation_in_progress"
  | "idempotency_conflict"
  | "revision_limit_reached"
  | "invalid_revision_request"
  | "revision_failed"
  | "retry_failed"
  | "composition_unavailable"
  | "composition_artifact_unavailable"
  | "service_unavailable";

const KNOWN_ERROR_CODES: ReadonlySet<string> = new Set<StudioErrorCode>([
  "validation_failed",
  "asset_empty",
  "unsupported_asset_type",
  "asset_type_mismatch",
  "asset_too_large",
  "invalid_asset_metadata",
  "upload_rate_limited",
  "asset_lifecycle_closed",
  "invalid_capability",
  "capability_subject_mismatch",
  "run_not_found",
  "invalid_run_state",
  "brand_lock_immutable",
  "brand_lock_unconfirmed",
  "locked_field_changed",
  "benefit_order_invalid",
  "localizable_fields_invalid",
  "invalid_analysis_input",
  "unsupported_analysis_scope",
  "provider_failed",
  "provider_output_invalid",
  "instruction_like_content",
  "prohibited_content",
  "unsafe_hypothesis",
  "draft_output_invalid",
  "composition_output_invalid",
  "critic_failed",
  "operation_in_progress",
  "idempotency_conflict",
  "revision_limit_reached",
  "invalid_revision_request",
  "revision_failed",
  "retry_failed",
  "composition_unavailable",
  "composition_artifact_unavailable",
  "service_unavailable",
]);

export class StudioApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: StudioErrorCode,
  ) {
    super("Studio request failed");
    this.name = "StudioApiError";
  }
}

export interface StudioApiClient {
  uploadAsset(file: File, metadata: UploadMetadata): Promise<AssetUploaded>;
  createRun(request: RunCreate): Promise<RunCreated>;
  analyzeRun(runId: string, token: string): Promise<AnalysisCompleted>;
  confirmBrandLock(
    runId: string,
    token: string,
    brandLock: BrandLock,
  ): Promise<BrandLockConfirmed>;
  generateDraft(runId: string, token: string): Promise<DraftGenerated>;
  generateComposition(runId: string, token: string): Promise<CompositionGenerated>;
  runCritic(runId: string, token: string): Promise<CritiqueCompleted>;
  submitFeedback(
    runId: string,
    token: string,
    request: FeedbackRequest,
    idempotencyKey: string,
  ): Promise<RevisionCompleted>;
  retryRevision(
    runId: string,
    token: string,
    request: RetryRequest,
    idempotencyKey: string,
  ): Promise<RevisionCompleted>;
  exportComposition(
    runId: string,
    token: string,
    version: 1 | 2,
    format: "png" | "json",
  ): Promise<Blob>;
  deleteAsset(assetId: string, token: string): Promise<void>;
}

type FetchLike = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

function bearer(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

function jsonHeaders(token?: string, idempotencyKey?: string): Record<string, string> {
  return {
    ...(token ? bearer(token) : {}),
    "Content-Type": "application/json",
    ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
  };
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function toApiError(response: Response): Promise<StudioApiError> {
  try {
    const value: unknown = await response.json();
    const detail = isObject(value) ? value.detail : undefined;
    const code = isObject(detail) ? detail.code : undefined;
    if (typeof code === "string" && KNOWN_ERROR_CODES.has(code)) {
      return new StudioApiError(response.status, code as StudioErrorCode);
    }
  } catch {
    // The public error remains generic for malformed or non-JSON bodies.
  }
  return new StudioApiError(response.status, "service_unavailable");
}

export function createStudioApiClient(
  configuredBaseUrl =
    process.env.NEXT_PUBLIC_CULTURESHIFT_API_URL ?? "http://127.0.0.1:8000",
  fetchImpl: FetchLike = fetch,
): StudioApiClient {
  const baseUrl = configuredBaseUrl.replace(/\/+$/, "");
  const endpoint = (path: string) => `${baseUrl}${path}`;

  async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await fetchImpl(endpoint(path), init);
    } catch {
      throw new StudioApiError(0, "service_unavailable");
    }
    if (!response.ok) throw await toApiError(response);
    if (!response.headers.get("content-type")?.toLowerCase().includes("application/json")) {
      throw new StudioApiError(response.status, "service_unavailable");
    }
    try {
      const value: unknown = await response.json();
      if (!isObject(value)) throw new Error("invalid response");
      return value as T;
    } catch {
      throw new StudioApiError(response.status, "service_unavailable");
    }
  }

  const runPath = (runId: string, suffix = "") =>
    `/api/v1/runs/${encodeURIComponent(runId)}${suffix}`;

  return {
    uploadAsset(file, metadata) {
      return requestJson<AssetUploaded>("/api/v1/assets", {
        method: "POST",
        body: file,
        headers: {
          "Content-Type": file.type,
          "X-Provenance-Ref": metadata.provenanceRef,
          "X-Rights-Ref": metadata.rightsRef,
        },
      });
    },
    createRun(request) {
      return requestJson<RunCreated>("/api/v1/runs", {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(request),
      });
    },
    analyzeRun(runId, token) {
      return requestJson<AnalysisCompleted>(runPath(runId, "/analyze"), {
        method: "POST",
        headers: bearer(token),
      });
    },
    confirmBrandLock(runId, token, brandLock) {
      return requestJson<BrandLockConfirmed>(
        runPath(runId, "/brand-lock/confirm"),
        {
          method: "POST",
          headers: jsonHeaders(token),
          body: JSON.stringify({ brand_lock: brandLock }),
        },
      );
    },
    generateDraft(runId, token) {
      return requestJson<DraftGenerated>(runPath(runId, "/draft"), {
        method: "POST",
        headers: bearer(token),
      });
    },
    generateComposition(runId, token) {
      return requestJson<CompositionGenerated>(runPath(runId, "/composition"), {
        method: "POST",
        headers: bearer(token),
      });
    },
    runCritic(runId, token) {
      return requestJson<CritiqueCompleted>(runPath(runId, "/critic"), {
        method: "POST",
        headers: bearer(token),
      });
    },
    submitFeedback(runId, token, request, idempotencyKey) {
      return requestJson<RevisionCompleted>(runPath(runId, "/feedback"), {
        method: "POST",
        headers: jsonHeaders(token, idempotencyKey),
        body: JSON.stringify(request),
      });
    },
    retryRevision(runId, token, request, idempotencyKey) {
      return requestJson<RevisionCompleted>(runPath(runId, "/retry"), {
        method: "POST",
        headers: jsonHeaders(token, idempotencyKey),
        body: JSON.stringify(request),
      });
    },
    async exportComposition(runId, token, version, format) {
      let response: Response;
      try {
        response = await fetchImpl(
          endpoint(`${runPath(runId, `/composition.${format}`)}?result_version=${version}`),
          { method: "GET", headers: bearer(token) },
        );
      } catch {
        throw new StudioApiError(0, "service_unavailable");
      }
      if (!response.ok) throw await toApiError(response);
      const mediaType = response.headers.get("content-type")?.split(";", 1)[0];
      const expected = format === "png" ? "image/png" : "application/json";
      if (mediaType !== expected) {
        throw new StudioApiError(response.status, "service_unavailable");
      }
      return response.blob();
    },
    async deleteAsset(assetId, token) {
      let response: Response;
      try {
        response = await fetchImpl(
          endpoint(`/api/v1/assets/${encodeURIComponent(assetId)}`),
          { method: "DELETE", headers: bearer(token) },
        );
      } catch {
        throw new StudioApiError(0, "service_unavailable");
      }
      if (!response.ok) throw await toApiError(response);
    },
  };
}
