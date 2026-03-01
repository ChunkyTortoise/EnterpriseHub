# Lyrio Visual Continuation Spec

## 1. Purpose
This spec defines the next implementation wave after the current visual redesign foundation. It is decision-complete for engineering, design QA, and release operations so work can continue without ambiguity.

## 2. Scope
In scope:
- Dashboard visual system hardening and production readiness
- Buyer portal UX refinement on real data
- Visual regression baseline automation
- Accessibility and responsive compliance verification
- Release sequencing and observability

Out of scope:
- New backend business logic beyond contract compatibility
- Replatforming frameworks
- Brand strategy changes beyond current premium-modern direction

## 3. Current Baseline (Implemented)
- Shared tokenized theme and typography for dashboard and portal
- Dashboard primitives and 3-region operator layout
- Buyer portal premium card hierarchy and session framing
- Standardized SwipeDeck prop contract
- Visual QA checklist and initial Playwright baseline test scaffold

## 4. Goals and Success Metrics
Primary goals:
- Raise perceived trust and polish
- Reduce operator friction in dashboard task flow
- Improve swipe-session completion in buyer portal
- Maintain visual consistency across both surfaces

Metrics:
- Dashboard command-to-action completion time: reduce by >= 20%
- Portal session completion rate: increase by >= 15%
- First-card portal drop-off: reduce by >= 10%
- Accessibility critical issues: 0 WCAG AA blockers
- Visual regression failures in release candidate: 0 untriaged

## 5. Architecture and Integration

### 5.1 Theme and Tokens
Source of truth:
- `/Users/cave/Projects/EnterpriseHub_new/frontend/src/app/globals.css`
- `/Users/cave/Projects/EnterpriseHub_new/ghl_real_estate_ai/frontend/styles/lyrio-theme.css`

Continuation requirements:
- Keep token names stable (`--lyr-*`)
- Move any newly introduced hardcoded colors into token references
- Avoid introducing parallel token namespaces

### 5.2 Component Boundaries
Dashboard primitives:
- `/Users/cave/Projects/EnterpriseHub_new/frontend/src/components/ui/*`

Portal UI:
- `/Users/cave/Projects/EnterpriseHub_new/ghl_real_estate_ai/frontend/components/portal/*`

Rule:
- Shared patterns (alert/badge/button semantics) must preserve naming and behavior parity even if implemented separately per package.

### 5.3 Portal Contract
`SwipeDeck` canonical interface:
- `properties?: array`
- `leadId?: string`
- `contactId?: string`
- `locationId?: string`
- `apiBaseUrl?: string`
- `onComplete?: () => void`
- `onError?: (error) => void`

Contract behavior:
- If `properties` provided and non-empty: render direct
- Else fetch from `GET {apiBaseUrl}/portal/deck` with `contact_id`, `lead_id`, `location_id`
- Swipes post to `POST {apiBaseUrl}/portal/swipe`

## 6. Work Plan (Continuation)

### Phase B: Hardening and Consistency
1. Refactor remaining inline style objects into class-based styles/tokens for maintainability.
2. Normalize spacing/typography usage in dashboard and portal against token scale.
3. Ensure all interactive controls satisfy 44x44 minimum hit area.
4. Add explicit disabled/hover/active/focus-visible states for all custom controls.

Deliverables:
- Reduced inline style footprint by >= 60% in redesigned files
- Style utilities documented in local README section

### Phase C: Route Integration and Real Data Validation
1. Wire portal components into host-app `/portal` production route.
2. Verify payloads against backend staging endpoint with real lead/property data.
3. Validate completion/empty/error states with production-like fixtures.

Deliverables:
- Route integration PR with screenshots
- Backend contract verification notes

### Phase D: Visual Regression and Accessibility Gates
1. Execute and stabilize Playwright screenshot suite:
   - dashboard-default
   - dashboard-active
   - dashboard-error
   - portal-first-card
   - portal-mid-session
   - portal-completion
2. Add keyboard-only smoke path for dashboard and portal action dock.
3. Run contrast checks for image overlays and status chips.

Deliverables:
- Baselines committed
- CI job or documented local gate command

### Phase E: Release and Monitoring
1. Release A: Foundation + dashboard + portal updates (current)
2. Release B: Integration hardening + regression gates
3. Release C: Post-launch UX/perf tuning

Post-launch monitoring:
- Portal swipe latency
- API error rate on `/portal/swipe`
- Dashboard interaction depth

## 7. Detailed UX Requirements

### Dashboard
- Left rail remains scannable at 1024px and collapses gracefully below 1200px
- Center stream preserves message provenance (bot/user) and timestamp visibility
- Sticky composer remains visible while stream scrolls
- Quick action chips remain keyboard focusable

### Portal
- Card overlay text must remain readable across bright/dark photos
- Progress framing always visible while deck active
- Action dock centered in thumb zone on mobile
- Feedback modal supports dismiss and skip with clear behavior

## 8. Accessibility Requirements
- WCAG AA contrast minimum for text/control labels
- Focus ring visible on all interactive elements
- Reduced-motion media query must meaningfully reduce animation motion
- ARIA labels present on icon-only controls

## 9. Performance Requirements
- No heavy blur/shadow combinations on core interactions
- Property images: `loading="lazy"` for non-initial cards
- Keep transition timings within:
  - Micro: 120-220ms
  - Screen/state: 280-360ms

## 10. Testing Plan

### Functional
- Swipe like/pass emits expected payload keys and values
- Feedback reason submission persists as pass feedback
- `onComplete` callback triggers at deck exhaustion

### Responsive
- 320px: no clipping, controls usable
- 768px: hierarchy and spacing preserved
- 1024px and 1440px: dashboard layout legible, no excessive stretch

### Visual Regression
- Use `/Users/cave/Projects/EnterpriseHub_new/tests/ui/visual-baseline.spec.ts`
- Baseline update policy:
  - Allowed only with explicit design change note
  - Must include before/after artifact in PR

## 11. Acceptance Criteria
A continuation release is accepted when all conditions are true:
1. Dashboard lint/build pass in `/frontend`
2. Portal lint/build gate pass in `/ghl_real_estate_ai/frontend`
3. Visual baseline suite runs and artifacts are reviewed
4. No P0/P1 accessibility defects open
5. QA checklist completed:
   - `/Users/cave/Projects/EnterpriseHub_new/docs/ui/VISUAL_QA_CHECKLIST.md`

## 12. Risks and Mitigations
Risk: Style drift from mixed inline/token styling
- Mitigation: Phase B class/token refactor and review checklist enforcement

Risk: Portal host integration mismatch
- Mitigation: Early route wiring and staging contract test

Risk: Snapshot flakiness
- Mitigation: Stable viewport/config and deterministic fixture data

## 13. PR and Change Management Requirements
Each PR must include:
- Scope summary
- Screenshots for changed states
- Accessibility notes
- Token usage confirmation
- Test evidence (lint/build/screenshot run)

## 14. Execution Checklist
- [ ] Complete Phase B refactor
- [ ] Integrate real `/portal` route
- [ ] Run and store visual baselines
- [ ] Complete accessibility smoke audit
- [ ] Validate metrics instrumentation paths
- [ ] Prepare Release B changelog and rollout notes
