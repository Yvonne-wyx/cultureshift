# CultureShift

CultureShift is a Cross-Cultural Creative Reasoning Studio for adapting static advertising concepts across cultural contexts while preserving verified brand truth.

## Status

CultureShift is in the planning and repository-bootstrap stage. It is not yet a production service and does not claim automated cultural validation.

## MVP scope

The MVP focuses on static ads for AI software and AI apps in two directions: China → UK and UK → China. Brand Lock preserves the logo, product name, verified product facts, real UI, benefit order, CTA action meaning, and layout template. Only narrative, use scenario, trust information, and language are localizable. Every cultural recommendation is a hypothesis, not a fact, and requires validation through appropriate research and human review.

Politics, medical, financial, gambling, tobacco, and child-targeted advertising are excluded.

## Architecture direction

The intended system separates upload and extraction, brand-locked representation, hypothesis-led cultural reasoning, creative generation, and human review. Privacy and public-boundary checks are applied throughout.

## Validation disclaimer

Outputs require human review and appropriate local research. CultureShift supports reasoning and creative exploration; it does not certify cultural correctness, legal compliance, or campaign performance.

## License boundary

Original source code is MIT licensed. Documentation, brand materials, and project-created non-code assets are not covered by that license unless explicitly stated. See [LICENSE_SCOPE.md](LICENSE_SCOPE.md).

## Repository check

On Windows, run the public-boundary verification without changing the machine execution policy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify-public-boundary.ps1
```

## Backend development

Install the package with development dependencies, then run the API locally:

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn cultureshift.app:app --host 127.0.0.1 --port 8000
```

The readiness endpoint is `GET /health`. Run automated checks with:

```powershell
python -m pytest
python -m ruff check .
```

## Fixture Studio demo

Day 18 provides a development-only launcher for the deterministic bilateral Studio. It does not connect to a live AI provider and must not be used with production data or configuration.

```powershell
npm --prefix apps/web run demo -- --check
npm --prefix apps/web run demo
```

Use `--backend-port`, `--frontend-port`, or `--root` to select loopback ports or a caller-managed runtime directory. The launcher validates both ports, waits for bounded backend and Studio readiness, terminates only its own child processes, and removes only a temporary root it created. See `docs/demo/day18-three-minute-walkthrough-v1.0.md` for the bounded walkthrough.
