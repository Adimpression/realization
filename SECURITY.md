# Security Policy

## Supported Versions

Realized is pre-1.0. Until a stable release policy exists, only the most recent
published release and the current development branch are eligible for security
fixes. Older snapshots may be useful for research comparison but are not
supported deployments.

## Reporting a Vulnerability

Do not disclose a suspected vulnerability in a public issue, discussion, test
fixture, corpus, or report artifact.

Report vulnerabilities privately to
[talktome@adimpression.mobi](mailto:talktome@adimpression.mobi). Include the
affected version or commit, reproduction conditions, expected impact, and
whether credentials or user data may have been exposed. Do not include working
secrets; rotate or revoke them first.

## Security-Sensitive Surfaces

Reports should identify whether they concern:

- host-operation realization or authority grants;
- ability installation, admission, matching, or invocation;
- SQLite state, persisted artifacts, receipts, or replay;
- provider credentials or model endpoints;
- imported source material, publication output, or path traversal;
- workstation RPC, browser, Flutter, Textual, or shell boundaries;
- dependency, build, packaging, or release integrity.

## Disclosure Process

The maintainers will reproduce and classify the report privately, identify the
smallest safe correction, run the relevant deterministic and qualification
gates, and coordinate disclosure after affected users have a remediation path.
No response-time commitment is made before a staffed public maintenance policy
exists.
