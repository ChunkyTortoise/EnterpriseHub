# Environment And Secret Policy

Last updated: 2026-05-06

EnterpriseHub keeps reviewer checks runnable without production credentials.

## 2026-05-17 Secret Scanner Update

Reviewer gates now include `python3 scripts/ci/secret_scan.py`, which scans tracked Python, Markdown, YAML, JSON, TOML, and related text files for real-looking API keys and credential assignments. Public docs must use placeholders such as `<OPENROUTER_API_KEY>` instead of realistic key-shaped values.

If any real credential was ever committed, rotate it in the provider console before treating the repo as clean. Removing the value from the current tree does not invalidate the exposed credential.

## Reviewer Checks

These commands must not require production secrets:

```bash
make verify-public
make verify-focused
```

If a local service needs credentials for deeper testing, use private environment variables or an untracked `.env` file.

## Demo Credentials

The demo credentials documented in `README.md` are synthetic demo-auth values. They are not production credentials and should not unlock real customer data.

## Environment Files

- Real `.env` files stay untracked.
- Deploy examples must use `.template` or `.example` suffixes.
- Template values must be obvious placeholders such as `<GHL_API_KEY>` or `${BASE64_ENCODED_JWT_SECRET}`.
- `JWT_SECRET_KEY` should be generated in the deployment environment, for example:

```bash
openssl rand -hex 64
```

## Production Secrets

Kubernetes secret manifests in this repo must remain templates only. Render real manifests outside git or through a CI/CD system connected to a secret manager.

## Backups

Database dumps and restore artifacts belong in private encrypted storage, not the repository. Keep backup procedures and sanitized examples in git; keep payloads out of git.

## Policy Gate

`python3 scripts/ci/tracked_artifact_policy.py` checks the working tree for tracked local artifacts, secret-shaped files, and generated payloads that should not appear in a public review.
