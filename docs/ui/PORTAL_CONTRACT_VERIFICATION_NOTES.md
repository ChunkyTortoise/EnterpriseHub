# Portal Contract Verification Notes

Date: February 21, 2026

## Canonical SwipeDeck Contract

Verified against `/Users/cave/Projects/EnterpriseHub_new/frontend/src/components/portal/SwipeDeck.tsx`:

- `properties?: array`
- `leadId?: string`
- `contactId?: string`
- `locationId?: string`
- `apiBaseUrl?: string`
- `onComplete?: () => void`
- `onError?: (error) => void`

## Behavior Verification

### 1) Direct render path (no fetch)
Condition:
- `properties` provided and non-empty.

Observed behavior:
- Deck renders from provided properties.
- No `GET {apiBaseUrl}/portal/deck` request issued.

Test coverage:
- `tests/ui/portal-contract.spec.ts` test `renders direct deck when properties are present and does not fetch`.

### 2) Fetch path
Condition:
- `properties` missing/empty and `contactId || leadId` available.

Observed behavior:
- Requests `GET {apiBaseUrl}/portal/deck` with query params:
  - `contact_id`
  - `lead_id`
  - `location_id`
- Supports payload keys `deck` or `properties`.

Test coverage:
- `tests/ui/portal-contract.spec.ts` first test captures request URL and asserts all params.

### 3) Swipe submission path
Action:
- Like/pass on active card.

Observed behavior:
- Posts to `POST {apiBaseUrl}/portal/swipe` with JSON payload:

```json
{
  "lead_id": "lead-123",
  "contact_id": "contact-123",
  "property_id": "p-100",
  "action": "like",
  "location_id": "loc-9"
}
```

Test coverage:
- `tests/ui/portal-contract.spec.ts` first test captures body and asserts canonical keys/values.

## Route-level C3 Scenarios

Implemented deterministic `/portal` query scenarios in `/Users/cave/Projects/EnterpriseHub_new/frontend/src/app/portal/page.tsx`:

- `?scenario=default`: standard deck behavior
- `?scenario=empty`: completion/empty state
- `?scenario=error`: forces fetch path against invalid API base to validate error state

## Visual Baseline Mapping (Phase D)

`/Users/cave/Projects/EnterpriseHub_new/tests/ui/visual-baseline.spec.ts` now captures:

- `dashboard-default`
- `dashboard-active`
- `dashboard-error`
- `portal-first-card`
- `portal-mid-session`
- `portal-completion`

## Staging Validation Status

- Local contract verification: complete (code + automated Playwright test definitions).
- Staging endpoint validation with real lead/property data: executed; blocked by route/auth mismatch in current staging environment (details below).

## Staging-backed Verification Run (February 21, 2026)

Environment used:
- Frontend host app: `http://127.0.0.1:4010`
- Staging API target used for verification: `http://127.0.0.1:8000`
- Lead/contact/location input used for run: `lead_001` / `lead_001` / `3xt4qayAh35BlDLaUv7P`

### Playwright staging contract test result

Command:

```bash
PORTAL_STAGING_API_BASE_URL=http://127.0.0.1:8000 \
PORTAL_STAGING_LEAD_ID=lead_001 \
PORTAL_STAGING_CONTACT_ID=lead_001 \
PORTAL_STAGING_LOCATION_ID=3xt4qayAh35BlDLaUv7P \
BASE_URL=http://127.0.0.1:4010 \
npx playwright test ../tests/ui/portal-contract.spec.ts --config=../tests/ui/playwright.config.ts
```

Observed:
- Local mocked contract tests passed.
- Staging-backed test failed waiting for `GET {apiBaseUrl}/portal/deck` (`deckStatus` remained `0` for 30s), meaning no successful browser-level response was received from the staging target in this environment.

### Direct staging API probe findings

Unauthenticated probes:
- `GET http://127.0.0.1:8000/portal/deck?...` → `404 resource_not_found`
- `POST http://127.0.0.1:8000/portal/swipe` → `404 resource_not_found`
- `GET http://127.0.0.1:8000/api/portal/deck/lead_001?...` → `401 authentication_required`
- `POST http://127.0.0.1:8000/api/portal/swipe` → `401 authentication_required`

Auth probe:
- `POST http://127.0.0.1:8000/api/auth/login` with `demo_user/demo_password` returned `authentication_required` with `Incorrect username or password` in debug detail for this running environment.

### Concrete conclusion

- The running staging backend currently exposes portal routes under `/api/portal/*` with JWT auth enforcement.
- Canonical host contract paths `/portal/deck` and `/portal/swipe` are not available directly on the staging backend (`404`), and browser-based staging contract verification cannot complete without an authenticated adapter path that matches the canonical frontend contract.
