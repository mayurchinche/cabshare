# Phase 0 Research: Premium UI/UX Across the Full App Journey

## 1. Design token approach

**Decision**: Plain TypeScript objects (`mobile/src/theme/tokens.ts`) exporting `colors`,
`spacing`, `typography`, `radii` constants, consumed via `StyleSheet.create` in each component —
no CSS-in-JS or theming library.

**Rationale**: React Native has no native CSS/Tailwind; a plain object module is the smallest
thing that works and is trivially typed/imported everywhere (ladder rung 6-7). Introducing a
theming library (e.g., `styled-components`, `restyle`) for 5 screens is unjustified complexity —
YAGNI.

**Alternatives considered**:
- *`react-native-paper` / `NativeBase` component library* — rejected: pulls in an entire opinionated
  component system + new dependency for a scope that's 5 screens and ~6 shared components; also
  makes "premium/on-brand" harder to hit precisely vs. hand-styled primitives.
- *StyleSheet inline per-screen (status quo)* — rejected: this is literally the bug being fixed
  (inconsistent/missing styling); a shared token module is the minimum fix for FR-001/FR-007.

## 2. Animation approach

**Decision**: React Native's built-in `Animated` API (already part of `react-native`, zero new
dependency) for the car-motion component: `Animated.loop(Animated.timing(...))` for the idle
motif, a one-shot `Animated.sequence` for the OTP/ride-confirm success transition.

**Rationale**: The spec's assumption explicitly scopes this to "a lightweight `Animated`/
`Reanimated`-driven car animation," not a produced illustration. `Animated` alone (no
`react-native-reanimated`, no `lottie-react-native`) is sufficient for a translating/scaling car
icon and is already installed — smallest dependency footprint (ladder rung 5: use what's already
there).

**Alternatives considered**:
- *`lottie-react-native` + a designed Lottie JSON* — rejected: requires either purchasing/finding
  a suitable Lottie asset or producing one, and adds a new native dependency; overkill for a
  simple translating car icon.
- *`react-native-reanimated`* — rejected: its main benefit (running animations on the UI thread
  for complex gesture-driven interactions) isn't needed for a simple linear/looping motion; adding
  it is a new native dependency for no measurable benefit here.

## 3. Reduce-motion handling

**Decision**: Use `AccessibilityInfo.isReduceMotionEnabled()` (React Native built-in) at mount
time to decide whether `CarMotion` renders its animated variant or a static icon/frame.

**Rationale**: Already part of React Native core, directly satisfies FR-005 with no new
dependency.

**Alternatives considered**: None needed — this is the standard, only built-in mechanism for this
check.

## 4. Segmented OTP input

**Decision**: Build `SegmentedCodeInput` as 6 individual single-character `TextInput`s in a row
with auto-advance-on-type/auto-back-on-delete logic (a well-known ~40-line RN pattern), backed by
one string value in the parent screen's state — no new dependency.

**Rationale**: A small, self-contained component is simpler and more controllable (custom
error/shake state per FR-006, styling per the shared token set) than pulling in a third-party OTP
input package, several of which exist but each adds a dependency for something this small
(ladder rung 6-7).

**Alternatives considered**:
- *`react-native-confirmation-code-field` or similar package* — rejected: an 8-line component
  implemented from `TextField` primitives is a smaller footprint than vetting/depending on a
  third-party package for this.
