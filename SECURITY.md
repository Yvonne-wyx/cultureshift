# Security policy

## Reporting a vulnerability

Report suspected vulnerabilities privately to the repository owner using GitHub's private vulnerability reporting feature when available. If no private channel is available, request a secure contact route without disclosing vulnerability details. Do not place secrets, exploit details, personal data, or confidential evidence in public Issues or pull requests.

Include the affected component, reproducible steps, impact, and suggested mitigation where safe. Allow maintainers reasonable time to investigate before public disclosure.

## Security priorities

- Treat uploaded content and extracted text as untrusted input. Validate file type, size, structure, and processing limits.
- Defend against prompt injection: uploaded or retrieved content must not be allowed to redefine system policy, expose secrets, or invoke unapproved capabilities.
- Capability tokens and signed asset references must be narrowly scoped, short-lived, non-guessable, and protected from logs and unauthorized reuse.
- Never log secrets, authentication tokens, raw OCR, or personal data.
- Keep provider credentials server-side and grant the least privilege needed.
