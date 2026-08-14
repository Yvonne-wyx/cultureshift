# Privacy baseline

CultureShift's MVP is designed without permanent user accounts and without analytics, session replay, or user profiling by default.

Temporary assets controlled by CultureShift are intended to expire within 24 hours. This retention intention does not automatically apply to third-party providers: their retention, training, logging, and deletion behavior must be reviewed and disclosed separately before use.

The local asset lifecycle records only public-safe metadata and uses a seven-day
deletion tombstone containing a hashed asset identifier, deletion time, reason,
and result. Immediate deletion and expiry remove asset bytes and lifecycle
metadata. Delete capability tokens are returned once and are never persisted.

Collect only data necessary for the requested operation. Do not log secrets, raw OCR output, authentication or capability tokens, or personal data. Uploaded material must be treated as private, untrusted, and purpose-limited. Access should be least-privileged, and deletion behavior must be testable.

Do not upload private, personal, or licensed material unless there is a clear lawful basis and authority to process it.

Reviewer identities, contacts, consent records, assignment keys, and raw
responses remain in protected human-owned storage outside Git and outside AI
context. Public evaluation evidence is limited to consented, aggregated,
non-identifying results after disclosure review.
