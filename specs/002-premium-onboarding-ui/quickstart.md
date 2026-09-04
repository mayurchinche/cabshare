# Quickstart: Premium UI/UX Across the Full App Journey

Manual + automated validation guide. No backend changes — assumes the Feature 001 app already
runs end-to-end on the Android emulator (per prior session: OTP request/confirm verified working).

## Prerequisites

- Metro running (`npx expo start --port 8081`), emulator booted, app installed — existing setup.
- No new native dependencies to install (research.md confirms zero new packages).

## Automated checks

```bash
cd mobile
npm test -- theme components/Button components/TextField components/SegmentedCodeInput components/Card components/EmptyState components/CarMotion
```

**Expect**: all new component unit tests pass, including:
- `Button` renders distinct styles for `default`/`pressed`/`disabled`/`loading` (FR-009).
- `TextField` shows error styling + message when `state="error"` (FR-002/FR-006).
- `SegmentedCodeInput` auto-advances focus on digit entry and auto-backs on delete.
- `CarMotion` renders a static fallback (no `Animated` calls) when
  `AccessibilityInfo.isReduceMotionEnabled` resolves `true` (FR-005).

## Manual smoke test on the Android emulator

1. Launch the app fresh → **Verification** screen shows the shared token palette/typography and
   an idle `CarMotion` animation (or static fallback if reduce-motion is on in emulator settings)
   — confirms User Story 1.
2. Enter a phone number, tap "Send OTP" → transition to OTP screen feels intentional (not an
   abrupt cut) — confirms User Story 3, scenario 1.
3. On the OTP screen, confirm the 6-digit input renders as segmented boxes, not a single field —
   confirms FR-003.
4. Enter the correct dev-mode OTP → a success `CarMotion` variant plays briefly before advancing —
   confirms User Story 2, scenario 2.
5. Enter an incorrect OTP → inline, friendly error text appears, input is easy to retry —
   confirms User Story 2, scenario 3.
6. Continue to Profile Setup → same palette/typography/spacing as prior screens — confirms User
   Story 3, scenario 2.
7. Post a ride intent, reach Match Review with zero matches → a designed empty state (icon + copy)
   appears, not a blank screen — confirms User Story 4, scenario 5.
8. Reach Ride Confirm → success-oriented visual treatment consistent with the OTP success motif —
   confirms User Story 4, scenario 3.
9. Reach Cancel → destructive action is visually distinct (warning color) but still on-brand, with
   a confirmation step — confirms User Story 4, scenario 4.
10. Toggle Android Settings → Accessibility → Remove animations (or equivalent), relaunch the app,
    repeat steps 1 and 4 → animations are skipped/minimized, but every button/input from steps 2-9
    remains fully usable — confirms FR-005 and SC-003.

## Regression check (must not break Feature 001)

11. Full OTP request → confirm → profile submit flow still succeeds end-to-end (reuse the exact
    steps already verified working in the prior debugging session) — confirms FR-008/SC-004.
