# Branch Protection Rules for EnterpriseHub

This document outlines the recommended GitHub branch protection rules.

## Overview

| Branch    | Purpose                         | Protection Level |
|-----------|--------------------------------|------------------|
| `main`    | Production-ready code          | Strict           |
| `develop` | Integration branch for features | Moderate         |

## Main Branch Protection

### Recommended Settings

| Setting | Value | Reason |
|---------|-------|--------|
| Require PR before merging | Yes | All changes go through review |
| Required approving reviews | 1 | At least one reviewer must approve |
| Dismiss stale reviews | Yes | New commits invalidate approvals |
| Require code owner reviews | Yes | CODEOWNERS controls reviewers |
| Require status checks | Yes | CI must pass before merge |
| Require up-to-date branch | Yes | Branch must be current with main |
| Allow force pushes | No | Preserve commit history |
| Allow deletions | No | Prevent accidental deletion |

### Required Status Checks

```
lint
test-unit (3.10)
test-unit (3.11)
test-integration
type-check
build
```

## Configuring via GitHub CLI

### Main Branch Protection

```bash
OWNER="ChunkyTortoise"
REPO="enterprise-hub"

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${OWNER}/${REPO}/branches/main/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "test-unit (3.10)", "test-unit (3.11)", "test-integration", "type-check", "build"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

### View Protection Rules

```bash
gh api "/repos/${OWNER}/${REPO}/branches/main/protection" | jq '.'
```

## GitHub Rulesets (Alternative)

Rulesets provide a newer, more flexible approach:

```bash
gh api \
  --method POST \
  "/repos/${OWNER}/${REPO}/rulesets" \
  -f name="Production Protection" \
  -f target="branch" \
  -f enforcement="active" \
  -f conditions='{"ref_name":{"include":["refs/heads/main"],"exclude":[]}}' \
  -f rules='[
    {"type":"deletion"},
    {"type":"non_fast_forward"},
    {"type":"pull_request","parameters":{"required_approving_review_count":1,"dismiss_stale_reviews_on_push":true,"require_code_owner_review":true}},
    {"type":"required_status_checks","parameters":{"strict_required_status_checks_policy":true,"required_status_checks":[{"context":"lint"},{"context":"test-unit (3.10)"},{"context":"test-unit (3.11)"},{"context":"build"}]}}
  ]'
```

## Troubleshooting

### Status checks not appearing

Status checks only appear after running once. Trigger a workflow:

```bash
gh workflow run ci.yml --ref main
```

### Check protection status

```bash
gh api "/repos/${OWNER}/${REPO}/branches/main" --jq '.protected'
```
