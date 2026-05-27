# EnterpriseHub Security Hardening, 2026-05-22

Triggered by: investigation of `codex/portal-api-idempotency-auth-hardening` divergence revealed 4 live secrets in public history. Full secret values are documented in tasks #2-5 of the session task list, not in this committed file.

## Secrets requiring rotation (4 confirmed live)

| # | Type | Identifier | Where | Rotation URL |
|---|---|---|---|---|
| 1 | GitHub PAT | `ghp_f0Vme0...` | 5+ commits, public branches `audit/recruiter-polish` and `dependabot/pip/main/python-minor-patch-06348069ff` | github.com/settings/tokens |
| 2 | JWT signing secret | `acHeQMn...` (commit dd67c447, file `ghl_real_estate_ai/api/data/.jwt_secret`) | Origin branches: chore/fiverr-gigs-published, codex/portal-api-idempotency-auth-hardening, codex/v6-week1-lane-a-foundation, feature/advanced-rag-benchmarks, fix/jorge-buyer-bot-test-contracts | Update JWT_SECRET_KEY env var; restart any service that signs/validates with it (jorge-real-estate-bots portal auth is the likely consumer) |
| 3 | Google API key | `AIzaSyBnqM...` (GitHub alert #4, file `contra_page_content.txt`, commit 41e214bb) | Public branches | console.cloud.google.com/apis/credentials |
| 4 | OpenRouter key | `sk-or-v1-64791d...` (GitHub alert #2, file `docs/kilo_code_openrouter_setup.md`, commit e4350a4c) | Public branches | openrouter.ai/keys |

GitHub secret-scanning alerts #1 (MongoDB test fixture with placeholder user:pass) and #3 (Stripe `whsec_` placeholder) appear to be false positives. Spot-check and dismiss.

## Why no history purge

- 1 fork exists (`justinseger015-ctrl/EnterpriseHub`). Force-push upstream does not clean their history.
- 8 OPEN PRs ride on affected branches: #29 codex/portal-api-idempotency-auth-hardening, #48 feat/hiring-signal-enhancement (active hiring branch), plus 6 dependabot PRs. Rewriting their base history breaks them.
- Rotation is the actual security fix; history purge is cosmetic and the cosmetic payoff is already lost the moment the fork was created.

## Server-side: enable GitHub Push Protection

GitHub already has secret-scanning alerts enabled (4 alerts visible). Push Protection, which blocks pushes that introduce new secrets instead of just alerting after, needs an explicit toggle.

Steps:

1. Visit https://github.com/ChunkyTortoise/EnterpriseHub/settings/security_analysis
2. Under "Secret scanning", enable "Push protection".
3. Verify "Secret scanning" itself shows "Enabled" (it does, given the existing alerts).

CLI alternative:

```bash
gh api -X PATCH repos/ChunkyTortoise/EnterpriseHub \
  -F security_and_analysis[secret_scanning_push_protection][status]=enabled
```

After enablement: any future push that introduces a recognized secret (GitHub PATs, AWS keys, Google service-account JSON, Stripe keys, etc.) is rejected at the server. Local pre-commit hooks remain useful, but Push Protection is the durable backstop.

## Local: fix the existing detect-secrets hook

Pre-commit config at `.pre-commit-config.yaml:10-21` runs Yelp `detect-secrets` against `.secrets.baseline`, but the baseline file does not exist. Result: the hook either errors or treats everything as a finding. Re-initialize:

```bash
cd /Users/cave/Projects/EnterpriseHub
pip install detect-secrets
detect-secrets scan --all-files > .secrets.baseline
git add .secrets.baseline
git commit -m "chore(security): add detect-secrets baseline"
pre-commit install   # ensure hook is wired into .git/hooks
pre-commit run detect-secrets --all-files
```

The baseline records known false positives so the hook only flags genuinely new secrets.

## .gitignore additions (minimal)

Current `.gitignore` already covers `_archive/`, `**/.jwt_secret`, `secrets/`, `.env*`, `*.key`, `*.pem`, etc. Genuine gaps based on this incident:

```gitignore
# Scraped page dumps (frequently contain pasted API keys from research browsing)
**/contra_*.txt
**/scraped_*.txt
**/page_content*.txt

# Common credential dotfiles
**/.openai
**/.openrouter
**/.anthropic

# Generic credential JSON
**/*credentials*.json
**/*service-account*.json
```

Lower priority. Not strictly needed once Push Protection is enabled, but cheap to add.

## Recurring discipline

- Treat any commit touching `_archive/`, `docs/*setup*.md`, or scraped content as a candidate for pre-commit review.
- When a Codex Cloud session rebases a branch and the local push is rejected, the safe default is "the cleaner side wins; inspect before forcing." That is what happened here.
- Public hiring repos: zero secrets in current HEAD is the bar. Old commits in history with rotated secrets are tolerable; live secrets in HEAD are not.
