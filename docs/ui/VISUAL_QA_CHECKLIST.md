# Lyrio Visual QA Checklist

## Typography
- [ ] `Space Grotesk` used for headings and high-emphasis display text.
- [ ] `Manrope` used for body copy and controls.
- [ ] Heading and body scale are consistent across dashboard and portal.

## Tokens
- [ ] Colors map to token variables only (no one-off hex values in component markup where avoidable).
- [ ] Radius values align to `8/12/16/24` token set.
- [ ] Shadows align to `sm/md/lg/elevated` token set.
- [ ] Core spacing aligns to `4/8/12/16/24/32/48`.

## States
- [ ] Dashboard has clear loading, error, empty, and active states.
- [ ] Portal has clear loading, error, empty/completion, and active swipe states.
- [ ] Async feedback uses branded alerts instead of generic text-only failures.

## Accessibility
- [ ] Every interactive control has visible focus indication.
- [ ] Touch controls are at least `44x44`.
- [ ] Text-over-image contrast remains readable on property cards.
- [ ] Reduced-motion mode preserves usability.

## Responsive
- [ ] 320px mobile width: no clipped content in dashboard and portal.
- [ ] 768px tablet width: layout and controls remain balanced.
- [ ] 1024px desktop width: dashboard 3-region layout remains legible.
- [ ] 1440px wide layout does not stretch content excessively.

## Interaction Integrity
- [ ] Swipe left/right still triggers backend sync payloads.
- [ ] Progress and reviewed counts are accurate during deck traversal.
- [ ] Dashboard command input and send action remain functional.
