# Day 4 Person B Bilateral Fixture Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to execute this plan one task at a time, and use `superpowers:test-driven-development` for every behavior change.

**Goal:** Deliver the Day 4 Person B T03A foundation: two rights-cleared, deterministic Orbit AI fixture bundles and a read-only bilateral preview, without implementing Day 5 composition or any live/provider behavior.

**Architecture:** Four project-created SVG assets are recorded in the fail-closed demo manifest. Two statically imported JSON bundles compose the generated Person A contracts into a fixture-only view model. A pure validation layer enforces direction, disclosure, rights, public-path, Brand Lock, and pending-review invariants before deeply freezing data. A server-compatible React component renders the validated bundles; the home page loads both stable IDs with no client state or network access.

**Tech Stack:** Next.js 16.3.0, React 19, TypeScript 5, JSON modules, Vitest 4, Testing Library, Python 3.11+, unittest/pytest, SVG, CSS.

## Global constraints

- Work only in `D:\create\Diversity\cultureshift\.worktrees\day4-person-a`.
- Preserve the exact UTF-8 disclosure `Fixture Demo / 非实时模型` in source, data, and rendered output.
- Use generated types from `apps/web/src/generated/contracts.ts`; do not duplicate `RunCreate`, `BrandLock`, `AssetRef`, or `CulturalHypothesis`.
- All fixture execution modes are `fixture`; no fetch, provider, upload, storage, telemetry, or live fallback is allowed.
- The renderer is read-only. Do not add Day 5 compositor, watermark export, result route, walkthrough, download, feedback, or retry features.
- Fixture validation errors must be exactly `Invalid fixture: <code>` and must never include submitted values or local paths.
- Use `apply_patch` for source edits. Every task follows RED → GREEN → focused verification → commit.
- After each implementation commit, run an independent specification review and then an independent code-quality review before starting the next task.

## Task 1: Create rights-cleared Orbit AI fixture assets

**Files:**

- Create: `apps/web/public/fixtures/orbit-ai/orbit-ai-logo.svg`
- Create: `apps/web/public/fixtures/orbit-ai/orbit-ai-product-ui.svg`
- Create: `apps/web/public/fixtures/orbit-ai/source-zh-cn.svg`
- Create: `apps/web/public/fixtures/orbit-ai/source-en-gb.svg`
- Modify: `demo/assets/manifest.json`
- Modify: `scripts/validate_demo_manifest.py`
- Modify: `tests/test_validate_demo_manifest.py`

### Step 1: Write failing manifest tests

Extend `valid_asset()` with real-file metadata:

```python
"asset_path": "apps/web/public/fixtures/orbit-ai/orbit-ai-logo.svg",
"sha256": "0" * 64,
```

Add tests proving the validator rejects:

```python
def test_rejects_missing_asset_path(self): ...
def test_rejects_absolute_or_traversing_asset_path(self): ...
def test_rejects_non_fixture_public_path(self): ...
def test_rejects_invalid_sha256(self): ...
```

Run:

```powershell
python -m pytest tests/test_validate_demo_manifest.py -q
```

Expected: the new rejection tests fail because path and digest are not yet validated.

### Step 2: Implement fail-closed manifest validation

Add pure helpers to `validate_demo_manifest.py`:

```python
import re
from pathlib import PurePosixPath

FIXTURE_ASSET_PREFIX = "apps/web/public/fixtures/"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")

def is_safe_fixture_asset_path(value):
    if not isinstance(value, str) or not value.startswith(FIXTURE_ASSET_PREFIX):
        return False
    if "\\" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    return path.is_absolute() is False and ".." not in path.parts
```

For every manifest asset, require `asset_path` to satisfy the helper and `sha256` to match the lowercase digest pattern. Keep the existing rights and provenance checks unchanged.

### Step 3: Create the four project-owned SVGs

Create deterministic, standalone SVG files with `viewBox`, accessibility `<title>`, flat shapes, and system-font text only:

- `orbit-ai-logo.svg`: a fictional orbital mark plus “Orbit AI”.
- `orbit-ai-product-ui.svg`: a non-functional task-summary panel.
- `source-zh-cn.svg`: synthetic zh-CN source ad with no real brand or customer.
- `source-en-gb.svg`: synthetic en-GB source ad with no real brand or customer.

Do not use `<script>`, `<foreignObject>`, external URLs, base64 content, remote fonts, tracking pixels, people, testimonials, performance metrics, or third-party marks.

Compute lowercase SHA-256 values from the committed bytes:

```powershell
Get-FileHash apps/web/public/fixtures/orbit-ai/*.svg -Algorithm SHA256 | Select-Object Path, Hash
```

### Step 4: Replace the metadata-only manifest entry

Write four individual cleared records, one per SVG. Each record must include its exact repository-relative `asset_path`, computed lowercase `sha256`, `project_created` ownership, `synthetic_example` provenance, repository-test/public-demo permission, permitted derivative/public display, no attribution requirement, and `demo/assets/RIGHTS.md` as evidence.

Use stable IDs:

```text
orbit-ai-logo-001
orbit-ai-product-ui-001
orbit-ai-source-zh-cn-001
orbit-ai-source-en-gb-001
```

### Step 5: Verify and commit

Run:

```powershell
python -m pytest tests/test_validate_demo_manifest.py -q
python scripts/validate_demo_manifest.py demo/assets/manifest.json
python -m ruff check scripts/validate_demo_manifest.py tests/test_validate_demo_manifest.py
git diff --check
git add apps/web/public/fixtures/orbit-ai demo/assets/manifest.json scripts/validate_demo_manifest.py tests/test_validate_demo_manifest.py
git commit -m "feat: add rights-cleared bilateral fixture assets"
```

Expected: all focused tests and validation pass; the manifest describes exactly the four real SVG files.

## Task 2: Implement bilateral fixture data and the pure loader

**Files:**

- Create: `apps/web/src/fixtures/types.ts`
- Create: `apps/web/src/fixtures/fixture-validation.ts`
- Create: `apps/web/src/fixtures/fixture-loader.ts`
- Create: `apps/web/src/fixtures/data/china-to-uk.json`
- Create: `apps/web/src/fixtures/data/uk-to-china.json`
- Create: `apps/web/src/fixtures/fixture-loader.test.ts`

### Step 1: Define tests before implementation

Create `fixture-loader.test.ts` with these RED cases:

```ts
expect(listFixtureIds()).toEqual(["china-to-uk", "uk-to-china"]);
expect(loadFixture("china-to-uk").request.direction).toBe("china_to_uk");
expect(loadFixture("uk-to-china").request.direction).toBe("uk_to_china");
expect(loadFixture("china-to-uk").request.execution_mode).toBe("fixture");
expect(loadFixture("china-to-uk").preview.brand_lock)
  .toEqual(loadFixture("uk-to-china").preview.brand_lock);
expect(Object.isFrozen(loadFixture("china-to-uk").preview.brand_lock)).toBe(true);
```

Test the internal pure validator with cloned raw values for `live_execution`, `unsafe_asset_path`, `rights_missing`, `brand_lock_mismatch`, and `hypothesis_not_pending`. Assert the full thrown messages, not just substrings, and assert that a secret sentinel placed in the bad value is absent from every error.

Run:

```powershell
npm.cmd --prefix apps/web test -- src/fixtures/fixture-loader.test.ts
```

Expected: import resolution fails because the fixture layer does not exist.

### Step 2: Define the fixture-only composition types

In `types.ts`, import generated `BrandLock`, `CulturalHypothesis`, and `RunCreate` and define:

```ts
export const FIXTURE_DISCLOSURE = "Fixture Demo / 非实时模型" as const;
export type FixtureId = "china-to-uk" | "uk-to-china";

export interface FixtureBundle {
  fixture_id: FixtureId;
  disclosure: typeof FIXTURE_DISCLOSURE;
  source_locale: "zh-CN" | "en-GB";
  target_locale: "zh-CN" | "en-GB";
  request: RunCreate;
  preview: {
    source_asset_path: string;
    logo_asset_path: string;
    product_ui_asset_path: string;
    source_copy: { headline: string; body: string };
    localized_copy: {
      locale: "zh-CN" | "en-GB";
      headline: string;
      body: string;
      cta_label: string;
      cta_action_meaning: string;
    };
    brand_lock: BrandLock;
    rule_ids: string[];
    hypotheses: CulturalHypothesis[];
    warnings: string[];
    limitation: string;
  };
}
```

### Step 3: Add the two deterministic JSON bundles

Use the same Brand Lock in both files:

```json
{
  "logo_asset_id": "a1111111-1111-4111-8111-111111111111",
  "product_name": "Orbit AI",
  "verified_product_facts": ["Turns approved notes into task summaries"],
  "product_ui_asset_ids": ["a2222222-2222-4222-8222-222222222222"],
  "benefit_order": ["Summarize", "Organize"],
  "cta_action_meaning": "Start a fixture demo",
  "layout_template_asset_id": "a3333333-3333-4333-8333-333333333333",
  "localizable_fields": ["narrative", "use_scenario", "trust_information", "language"]
}
```

The request and preview must each contain that exact value. Use valid RFC 4122 version-4 IDs for all contract IDs. Set source assets to `kind: "source_ad"`, use only public references such as `fixture:orbit-ai-source-zh-cn-001` and `rights:demo-assets-manifest`, and set `execution_mode: "fixture"`.

Direction-specific content:

- `china-to-uk.json`: `china_to_uk`, source `zh-CN`, target `en-GB`, rules `ZEU-S1` and `ZEU-S3`, pending hypothesis `ZEU-H1`.
- `uk-to-china.json`: `uk_to_china`, source `en-GB`, target `zh-CN`, rules `EZC-S1` and `EZC-S3`, pending hypothesis `EZC-H1`.

Each hypothesis must include evidence references, uncertainty, validation requirements, and `review_status: "pending"`. Each preview must include `HUMAN_REVIEW_REQUIRED` and a limitation explicitly stating that the proposal is not cultural, legal, or performance validation.

### Step 4: Implement validation and immutable loading

In `fixture-validation.ts`, expose an internal `validateFixture(raw: unknown, expectedId: FixtureId): Readonly<FixtureBundle>` for focused tests. Validate plain-object shape before reading nested fields. Use a stable error helper:

```ts
function invalid(code: string): never {
  throw new Error(`Invalid fixture: ${code}`);
}
```

Enforce the complete invariant list from the approved design. Public asset paths must start `/fixtures/orbit-ai/`, contain no backslash, URL scheme, query/fragment, `.` or `..` segments, and end in `.svg`. Approved references must start `fixture:`, `rights:`, or `evidence:`. Compare Brand Lock with stable structural equality after validating it is an object. Reject every hypothesis whose status is not `pending` or whose evidence/validation arrays are empty.

Recursively freeze arrays and objects:

```ts
function deepFreeze<T>(value: T): Readonly<T> {
  if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
    for (const child of Object.values(value as Record<string, unknown>)) deepFreeze(child);
    Object.freeze(value);
  }
  return value as Readonly<T>;
}
```

In `fixture-loader.ts`, statically import both JSON files, keep them in an immutable record, return the stable ID tuple, reject unknown runtime IDs as `Invalid fixture: unknown_id`, and validate on every load. Do not call `fetch`, `XMLHttpRequest`, a provider, or the backend.

### Step 5: Verify and commit

Run:

```powershell
npm.cmd --prefix apps/web test -- src/fixtures/fixture-loader.test.ts
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run contracts:check
git diff --check
git add apps/web/src/fixtures
git commit -m "feat: add deterministic bilateral fixture loader"
```

Expected: all fixture tests pass, generated contracts remain current, and TypeScript accepts both JSON documents through the validated boundary.

## Task 3: Build the read-only FixturePreview component

**Files:**

- Create: `apps/web/src/components/fixture-preview.tsx`
- Create: `apps/web/src/components/fixture-preview.module.css`
- Create: `apps/web/src/components/fixture-preview.test.tsx`

### Step 1: Write the component tests

Load each real fixture through the loader and assert the component renders:

- direction and source/target locales;
- the source SVG via a `/fixtures/orbit-ai/` path;
- localized headline, body, and CTA;
- `Orbit AI` and all protected facts;
- rule IDs and pending hypothesis IDs;
- `Human review required`;
- the exact disclosure once per component;
- the limitation without words claiming approval, correctness, compliance, or uplift.

Also assert there are no buttons, links, editable fields, or `data-watermark` claims.

Run:

```powershell
npm.cmd --prefix apps/web test -- src/components/fixture-preview.test.tsx
```

Expected: component import resolution fails.

### Step 2: Implement the server-compatible renderer

Implement:

```tsx
export function FixturePreview({ fixture }: { fixture: Readonly<FixtureBundle> }) {
  // semantic article, header, source creative, proposal, Brand Lock,
  // rule/hypothesis traceability, human-review warning, disclosure
}
```

Use semantic headings and lists. Give the article an accessible name derived from its direction. Render the source asset with `next/image` and explicit dimensions; the logo and product UI may be compact supporting images. Add no `"use client"`, hooks, event handlers, forms, links, buttons, mutable state, or data fetching.

Keep component CSS local. Use a neutral high-contrast card, a clear pending-review badge, responsive single-column fallback, and visible focus-independent disclosure. The design must remain legible at 320px width and in dark preference without relying on colour alone.

### Step 3: Verify and commit

Run:

```powershell
npm.cmd --prefix apps/web test -- src/components/fixture-preview.test.tsx
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
git diff --check
git add apps/web/src/components
git commit -m "feat: render read-only fixture previews"
```

Expected: component tests, typecheck, and lint pass; no interactive or Day 5 behavior is present.

## Task 4: Present both fixtures on the Day 4 foundation page

**Files:**

- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/page.test.tsx`
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/src/app/layout.tsx`

### Step 1: Replace the placeholder test with bilateral integration tests

Write tests asserting:

```ts
expect(screen.getByRole("heading", { name: "CultureShift bilateral fixture lab" }))
  .toBeInTheDocument();
expect(screen.getByRole("article", { name: /China to UK/ })).toBeInTheDocument();
expect(screen.getByRole("article", { name: /UK to China/ })).toBeInTheDocument();
expect(screen.getAllByText("Fixture Demo / 非实时模型")).toHaveLength(2);
expect(screen.getAllByText("Human review required")).toHaveLength(2);
```

Assert the page contains no buttons, file inputs, live-model wording, performance-uplift claim, or “approved” claim.

Run:

```powershell
npm.cmd --prefix apps/web test -- src/app/page.test.tsx
```

Expected: tests fail against the contract-only placeholder page.

### Step 2: Implement the bilateral server page

Load fixtures synchronously from the stable IDs and render them:

```tsx
const fixtures = listFixtureIds().map(loadFixture);

export default function Home() {
  return (
    <main className="fixture-lab">
      <header>...</header>
      <section aria-label="Bilateral fixture previews">
        {fixtures.map((fixture) => (
          <FixturePreview key={fixture.fixture_id} fixture={fixture} />
        ))}
      </section>
    </main>
  );
}
```

Update metadata to describe the bilateral fixture lab. Replace the scaffold dark-mode inversion with a deliberate, accessible visual system shared by the lab while leaving card-specific styling in the CSS module. Keep the page static and server-compatible.

### Step 3: Run the complete Person B and repository gates

Run in this order:

```powershell
python -m pytest -q
python -m ruff check .
python scripts/validate_demo_manifest.py demo/assets/manifest.json
python scripts/export_contracts.py --check
npm.cmd --prefix apps/web run contracts:check
npm.cmd --prefix apps/web test
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run lint
$env:NEXT_TELEMETRY_DISABLED="1"; npm.cmd --prefix apps/web run build
npm.cmd --prefix apps/web audit --audit-level=high
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify-public-boundary.ps1
git diff --check
git status --short
```

Expected:

- all Python and web tests pass;
- schema and generated TypeScript are current;
- typecheck, lint, production build, audit, and public-boundary scan pass;
- the build has no runtime fetch/provider dependency;
- only intended Person B files are uncommitted.

### Step 4: Commit the integrated page

```powershell
git add apps/web/src/app
git commit -m "feat: present Day 4 bilateral fixture lab"
```

Then request an independent final code review over the complete Person B commit range. Address verified findings with TDD and rerun every affected gate before declaring Person B Day 4 complete.

## Completion handoff

After the final review is clean:

1. Record exact commit IDs and verification results in the Day 4 work ledger.
2. Generate `D:\create\Diversity\Day4.docx` in the same visual/content format as Days 1–3, covering both Person A and Person B work.
3. Render the DOCX to page images and visually verify every page.
4. Integrate the reviewed branch into local `main` without discarding unrelated user work.
5. Rerun the complete repository gates from the integrated `main` checkout.
6. Push `main` directly to `https://github.com/Yvonne-wyx/cultureshift` under the user's prior authorization.
7. Confirm the remote `main` SHA and report the local Day 4 document path.
