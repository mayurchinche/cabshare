# Tasks: Premium UI/UX Across the Full App Journey

**Input**: Design documents from `/specs/002-premium-onboarding-ui/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present; no
`contracts/` — purely internal mobile UI, no external interface)

**Tests**: Component-level unit tests are included since they're cheap/fast for pure-presentation
components and directly validate FR-005/FR-009 state handling; no contract/integration tests
needed (no backend/API surface).

**Organization**: Tasks are grouped by user story (US1-US4) per spec.md priorities.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Create `mobile/src/theme/tokens.ts` exporting `colors`, `spacing`, `typography`, `radii` per data-model.md `DesignTokens` shape
- [ ] T002 [P] Create `mobile/src/theme/index.ts` barrel export for the theme module

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No screen restyling can begin until the shared components exist

- [ ] T003 [P] Create `Button` component in `mobile/src/components/Button.tsx` with `variant` (`primary`/`secondary`/`destructive`) and `state` (`default`/`pressed`/`disabled`/`loading`) props, consuming `theme/tokens.ts` (FR-009)
- [ ] T004 [P] Create `TextField` component in `mobile/src/components/TextField.tsx` with `state` (`default`/`focused`/`error`) and `errorMessage` props (FR-002)
- [ ] T005 [P] Create `SegmentedCodeInput` component in `mobile/src/components/SegmentedCodeInput.tsx`: 6 single-character `TextField`s with auto-advance/auto-back and `error` shake state (FR-003, FR-006)
- [ ] T006 [P] Create `Card` component in `mobile/src/components/Card.tsx` with `variant` (`default`/`match`/`destructive`) prop (FR-010)
- [ ] T007 [P] Create `EmptyState` component in `mobile/src/components/EmptyState.tsx` with `title`/`body`/`icon` props (FR-010)
- [ ] T008 Create `CarMotion` component in `mobile/src/components/CarMotion.tsx`: `variant` (`idle`/`success`) prop, uses `Animated.loop`/`Animated.sequence`, reads `AccessibilityInfo.isReduceMotionEnabled()` at mount to render a static fallback when true (FR-004, FR-005)

**Checkpoint**: Shared component library ready — screen restyling can now begin

---

## Phase 3: User Story 1 - First impression during phone verification (Priority: P1) 🎯 MVP

**Goal**: Verification screen uses the shared design system + idle `CarMotion`.

**Independent Test**: Launch app fresh, reach Verification screen, visually confirm token-based
styling and idle animation (or static fallback under reduce-motion) per quickstart.md step 1.

### Implementation for User Story 1

- [ ] T009 [US1] Restyle the phone-number `TextField` and "Send OTP" `Button` in `mobile/src/screens/Verification.tsx` using the new shared components, removing the ad-hoc inline styles added during the earlier debugging session
- [ ] T010 [US1] Add an idle `CarMotion` above the phone-number field in `mobile/src/screens/Verification.tsx`
- [ ] T011 [US1] Apply `theme/tokens.ts` spacing/typography to the screen container and heading in `mobile/src/screens/Verification.tsx`

**Checkpoint**: US1 fully functional and independently testable

---

## Phase 4: User Story 2 - Reassuring OTP verification moment (Priority: P1)

**Goal**: OTP entry uses `SegmentedCodeInput`, a success `CarMotion`, and friendly inline errors.

**Independent Test**: Request an OTP, enter correct/incorrect codes, confirm segmented input,
success animation, and inline error text per quickstart.md steps 3-5.

### Implementation for User Story 2

- [ ] T012 [US2] Replace the plain OTP `TextInput` in `mobile/src/screens/Verification.tsx` with `SegmentedCodeInput`
- [ ] T013 [US2] On correct OTP confirm, play the `CarMotion` `success` variant before navigating forward, in `mobile/src/screens/Verification.tsx`
- [ ] T014 [US2] On incorrect OTP, show inline friendly error text below `SegmentedCodeInput` and clear the input for retry, in `mobile/src/screens/Verification.tsx`
- [ ] T015 [US2] Add a "Resend code" action with a visible cooldown timer to `mobile/src/screens/Verification.tsx`

**Checkpoint**: US1 + US2 both independently functional

---

## Phase 5: User Story 4 - Consistent premium design across posting, matching, and ride screens (Priority: P1)

**Goal**: PostIntent, MatchReview, RideConfirm, Cancel all consume the same shared components/tokens.

**Independent Test**: Log in, post intent, view matches, confirm, cancel — visually confirm
consistent token usage and no unstyled default components, per quickstart.md steps 7-9.

### Implementation for User Story 4

- [ ] T016 [P] [US4] Restyle all inputs in `mobile/src/screens/PostIntent.tsx` using `TextField`/`Button` from the shared component library (FR-001)
- [ ] T017 [P] [US4] Restyle `mobile/src/screens/MatchReview.tsx` to render each candidate match as a `Card` (avatar/initials, route summary, match reason) instead of a plain list row
- [ ] T018 [US4] Add an `EmptyState` to `mobile/src/screens/MatchReview.tsx` for the zero-matches case
- [ ] T019 [P] [US4] Restyle `mobile/src/screens/RideConfirm.tsx` with a success-oriented `Card`/`CarMotion` (`success` variant) consistent with the OTP success motif
- [ ] T020 [P] [US4] Restyle `mobile/src/screens/Cancel.tsx` using the `destructive` `Card`/`Button` variants, with an explicit confirmation step before cancelling

**Checkpoint**: All screens now share one consistent premium design language

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T021 [P] Add unit tests for `Button` state variants in `mobile/tests/unit/components/Button.test.tsx`
- [ ] T022 [P] Add unit tests for `TextField` state variants in `mobile/tests/unit/components/TextField.test.tsx`
- [ ] T023 [P] Add unit tests for `SegmentedCodeInput` auto-advance/auto-back behavior in `mobile/tests/unit/components/SegmentedCodeInput.test.tsx`
- [ ] T024 [P] Add a reduce-motion fallback test for `CarMotion` in `mobile/tests/unit/components/CarMotion.test.tsx` (mocks `AccessibilityInfo.isReduceMotionEnabled` to resolve `true`, asserts no `Animated` loop starts)
- [ ] T025 Run `specs/002-premium-onboarding-ui/quickstart.md` end-to-end on the Android emulator, including the regression check (step 11) against the previously-verified OTP request/confirm flow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all screen restyling (every story needs the shared components).
- **US1 (Phase 3)**: Depends on Foundational only.
- **US2 (Phase 4)**: Depends on Foundational + US1 (same screen file, `SegmentedCodeInput`/`CarMotion` build on US1's restyle of `Verification.tsx`).
- **US4 (Phase 5)**: Depends on Foundational only — independent of US1/US2 (different screen files: PostIntent/MatchReview/RideConfirm/Cancel vs. Verification), can run in parallel with Phases 3-4 by a second developer.
- **Polish (Phase 6)**: Depends on all desired stories being complete.

### Parallel Opportunities

- T003-T007 (Foundational shared components) all in parallel — different files.
- Phase 5 (US4) can run entirely in parallel with Phases 3-4 (US1/US2) since they touch different screen files.
- T016, T017, T019, T020 within US4 in parallel — different screen files.
- T021-T024 (Polish tests) in parallel.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Setup + Foundational (shared components — this is most of the actual "premium" work).
2. US1 (Verification screen) → validate independently → this alone already demonstrates the new
   design language to a sponsor.
3. Add US2, then US4, each independently demoable.

### Incremental Delivery

Setup+Foundational → US1 → US2 → US4 (can parallelize with US1/US2 if staffed) → Polish.
