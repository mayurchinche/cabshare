# Implementation Plan: Premium UI/UX Across the Full App Journey

**Branch**: `002-premium-onboarding-ui` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-premium-onboarding-ui/spec.md`

## Summary

Introduce one shared design-token module (colors, type scale, spacing, radii) consumed by every
existing screen (`Verification`, `PostIntent`, `MatchReview`, `RideConfirm`, `Cancel`), replacing
ad-hoc/unstyled components with a small set of reusable styled primitives (`Button`, `TextField`,
`Card`, `EmptyState`). A single lightweight car-motion component (built on React Native's built-in
`Animated` API — no new animation library) provides the idle "car en route" motif on Verification
and a success-transition motif after OTP confirm and Ride Confirm, honoring the OS reduce-motion
setting. No backend changes; purely a mobile-app visual/component layer.

## Technical Context

**Language/Version**: TypeScript, React Native 0.81 (existing `mobile/` app, unchanged)

**Primary Dependencies**: React Native's built-in `Animated` API and `AccessibilityInfo` (for
reduce-motion detection) — both already part of the existing `react-native` dependency, no new
package added. React Navigation (existing, for the P2 "intentional transition" acceptance
scenario).

**Storage**: N/A — no data model changes; this feature is presentation-only

**Testing**: Jest + React Native Testing Library (existing) — snapshot/behavior tests for the new
shared components (`Button`, `TextField`, `Card`, `EmptyState`) and a reduce-motion fallback test
for the car-motion component

**Target Platform**: Existing Android emulator test setup (iOS deferred per prior discussion,
unchanged)

**Project Type**: mobile-app only (no `api/` changes)

**Performance Goals**: Idle animation must not drop the UI thread below 30fps on the existing
Pixel-profile Android emulator; screens must remain interactive (typeable/tappable) even if the
animation fails to mount

**Constraints**: Zero new npm dependencies (design tokens + `Animated` are sufficient — see
research.md); zero backend changes; must not regress the already-verified working OTP
request/confirm flow (FR-008)

**Scale/Scope**: 5 existing screens restyled (`Verification`, `PostIntent`, `MatchReview`,
`RideConfirm`, `Cancel`) + 4 new shared components + 1 motion component

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Privacy by Default | Purely visual layer; no change to what data is fetched/displayed/masked. | PASS |
| II. Safety-First Matching | No change to verification/masking/confirm logic, only its presentation. | PASS |
| III. Radius & Matching Integrity | No matching-logic changes. | PASS |
| IV. Partner-Agnostic Booking Abstraction | No booking-provider changes. | PASS |
| V. Transparent, Simple Monetization | Fare-split display becomes a styled `Card`, but the underlying line-item data/values are unchanged — still itemized, not collapsed into one total. | PASS |
| VI. Cross-Platform Parity & MVP Discipline | Single shared component set used by the one React Native codebase; no platform-specific styling forks; scope stays to existing screens (YAGNI — no new screens invented for this feature). | PASS |

No violations — Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-premium-onboarding-ui/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command) — N/A content, no data entities
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command) — N/A, no external interface
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
mobile/
├── src/
│   ├── theme/                  # NEW: tokens.ts (colors, type scale, spacing, radii), index.ts
│   ├── components/
│   │   ├── Button.tsx          # NEW: shared button (default/pressed/disabled/loading states — FR-009)
│   │   ├── TextField.tsx       # NEW: shared input (default/focused/error states — FR-002)
│   │   ├── SegmentedCodeInput.tsx  # NEW: 6-box OTP input (FR-003)
│   │   ├── Card.tsx            # NEW: shared card container (used by MatchReview, fare-split)
│   │   ├── EmptyState.tsx      # NEW: illustration + copy for empty match lists etc. (FR-010)
│   │   └── CarMotion.tsx       # NEW: Animated-based car-en-route motif, idle + success variants (FR-004/FR-005)
│   └── screens/                # EXISTING, restyled in place: Verification, PostIntent, MatchReview, RideConfirm, Cancel
└── tests/
    └── unit/                   # + component tests for the above
```

**Structure Decision**: No new top-level project; all changes are additive files under the
existing `mobile/src/` tree (new `theme/` module + new shared `components/`), plus in-place
restyling of the 5 existing screen files. No `api/` changes.

## Complexity Tracking

> No Constitution Check violations — this section intentionally left empty.
