# Feature Specification: Premium UI/UX Across the Full App Journey

**Feature Branch**: `002-premium-onboarding-ui`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "It's not about the signup page, it's about the user journey throughout the application on every page. Redesign every screen — phone verification, OTP, profile setup, posting a ride intent, viewing matches, ride confirmation, cancellation — with a premium, on-brand visual design and a delightful ride-themed animation (a cab/train traveling toward the user). The UI must become the app's standout selling point, presentable to sponsors."

**Scope note**: This spec originally covered only the verification/OTP/profile screens (User Stories 1-3 below). It is now expanded to the entire app: every screen the rider sees (Verification → OTP → Profile Setup → Post Ride Intent → Match Review → Ride Confirm → Cancel) must share one consistent premium design system. User Stories 1-3 remain valid for onboarding; User Story 4 extends the same treatment app-wide.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First impression during phone verification (Priority: P1)

A new rider opens the app for the first time and lands on the phone number entry screen. Instead of a bare text box and button, they see a polished, branded screen with clear visual hierarchy, a friendly illustration/animation reinforcing "your ride is on its way," and confidence-inspiring micro-copy.

**Why this priority**: This is the very first screen every user (and every sponsor/demo viewer) sees. It sets the tone for the entire product's perceived quality.

**Independent Test**: Launch the app fresh (no session) and reach the phone entry screen. Can be judged purely on visuals/interaction polish without touching any other screen.

**Acceptance Scenarios**:

1. **Given** a first-time user opens the app, **When** the verification screen loads, **Then** they see a branded layout (logo/wordmark, consistent color palette, spacing, typography) instead of unstyled default components.
2. **Given** the phone entry screen is visible, **When** the user taps the input field, **Then** the field shows clear focus styling and the keyboard/input works without confusion.
3. **Given** the user is on the phone entry screen, **When** the screen is idle, **Then** a subtle looping animation (e.g., a car icon moving along a path) plays to reinforce the ride-matching concept without being distracting or blocking interaction.

---

### User Story 2 - Reassuring OTP verification moment (Priority: P1)

After requesting an OTP, the user sees a screen that clearly communicates "code sent," offers an obvious place to enter the 6-digit code, and gives immediate, friendly feedback on success or failure (e.g., a satisfying "confirmed" animation vs. a clear, non-scary error state).

**Why this priority**: OTP entry is the most error-prone, drop-off-heavy step in any phone-auth flow; a premium feel here directly affects completion rate.

**Independent Test**: Trigger an OTP send and interact with the code entry screen in isolation (valid code, invalid code, resend).

**Acceptance Scenarios**:

1. **Given** an OTP was just requested, **When** the OTP screen appears, **Then** it clearly shows the destination phone number and an obviously distinct 6-digit code input (segmented boxes, not a plain single-line field).
2. **Given** the user enters the correct code, **When** they submit, **Then** a brief success animation/transition plays before advancing (e.g., the car "arrives").
3. **Given** the user enters an incorrect code, **When** they submit, **Then** the error is shown inline with clear, non-technical language and the input is easy to retry (auto-clear or shake feedback).
4. **Given** the user wants a new code, **When** they tap "resend," **Then** they get clear feedback (cooldown timer, confirmation) without needing to reload the screen.

---

### User Story 3 - Cohesive "getting a ride" motion motif (Priority: P2)

Across the verification → OTP → profile setup flow, a consistent lightweight motion/illustration motif (a car en route, converging toward the user) ties the screens together, so sponsors/demo viewers perceive one polished product rather than disconnected screens.

**Why this priority**: Elevates the flow from "styled screens" to a cohesive branded experience — the primary differentiator the user asked for, but depends on P1 screens existing first.

**Independent Test**: Step through verification → OTP → profile screens back-to-back and confirm consistent visual language (same palette, spacing scale, motion style) without needing backend changes.

**Acceptance Scenarios**:

1. **Given** the user completes phone entry, **When** they transition to the OTP screen, **Then** the transition itself feels intentional (animated handoff, not an abrupt jump cut).
2. **Given** the user completes OTP verification, **When** they land on profile setup, **Then** the same design language (colors, type, spacing, iconography) is visibly continued.

---

### User Story 4 - Consistent premium design across posting, matching, and ride screens (Priority: P1)

Beyond onboarding, a rider posting a ride intent, browsing candidate matches, confirming a ride, or cancelling one must experience the same premium visual language (palette, type, spacing, motion motif) as the onboarding flow — not a jump back to plain default components.

**Why this priority**: The onboarding screens are seen once; the post-intent/match/ride screens are used repeatedly and are what a sponsor demo would actually dwell on. Without this, the "premium" impression from onboarding is undermined immediately after login.

**Independent Test**: Log in with a verified test user, post a ride intent, view the match list, confirm a ride, and cancel a ride — each screen can be visually inspected independently against the shared design token set.

**Acceptance Scenarios**:

1. **Given** a logged-in rider on the Post Ride Intent screen, **When** the screen loads, **Then** all inputs (location fields, time picker) use the shared styled input treatment (border, focus state, spacing) — no unstyled default `TextInput`/`Picker`.
2. **Given** the rider submits a ride intent, **When** matches are found, **Then** the Match Review screen presents each candidate match as a styled card (avatar/initials, route summary, match score/reason) rather than a plain list row.
3. **Given** a rider selects a match, **When** they reach Ride Confirm, **Then** the confirmation screen uses a clear success-oriented visual treatment (icon/animation) consistent with the OTP-success motion motif from onboarding.
4. **Given** a rider wants to cancel a confirmed ride, **When** they reach the Cancel screen, **Then** the destructive action is visually distinct (warning color/copy) but still on-brand, with a confirmation step to avoid accidental cancellation.
5. **Given** any of these screens has no data yet or an empty state (e.g., no matches found), **When** displayed, **Then** it shows a designed empty state (illustration + friendly copy) instead of a blank screen.

---

### Edge Cases

- What happens on low-end devices/emulators where animations may be janky? → Animation must degrade gracefully (reduced motion / simplified fallback) rather than block core actions (submit buttons must remain usable even if animation fails to render).
- How does the system handle a user with system-level "reduce motion" accessibility setting enabled? → Looping/decorative animations must be skipped or minimized while functional transitions remain.
- What happens if the OTP request/network fails during the visual flow? → Error state must still be legible and actionable within the new visual design (no more silent/plain failures).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every rider-facing screen (Verification, OTP, Profile Setup, Post Ride Intent, Match Review, Ride Confirm, Cancel) MUST use one consistent, defined visual design system (color palette, typography scale, spacing scale, corner radii) instead of unstyled default components.
- **FR-002**: The phone number input MUST have clear visible styling in all states (default, focused, error) with sufficient contrast and touch target size.
- **FR-003**: The OTP entry MUST use a segmented multi-box code input (one digit per box) rather than a single plain text field.
- **FR-004**: The flow MUST include a branded car/ride-themed animation that plays: (a) idle/looping on the phone entry screen, and (b) as a success transition after correct OTP entry.
- **FR-005**: All animations MUST respect the OS-level "reduce motion" accessibility setting by falling back to a static or minimal-motion equivalent.
- **FR-006**: Error states (invalid OTP, network failure, validation errors) MUST be presented with friendly, non-technical copy and a visually distinct (but on-brand) treatment, never a raw/default error look.
- **FR-007**: The visual design (palette, type, spacing) MUST remain visually consistent across all rider-facing screens app-wide, not just onboarding.
- **FR-008**: The redesigned screens MUST remain fully functional (typeable, submittable, navigable) on the existing Android emulator test environment without regressing the already-working OTP request/confirm flow.
- **FR-009**: Buttons and primary CTAs MUST have distinct default/pressed/disabled/loading visual states.
- **FR-010**: Match Review, empty states, and destructive actions (Cancel) MUST each have a designed, on-brand treatment (styled card, illustrated empty state, warning-but-branded destructive style) rather than falling back to default components.

### Key Entities

- **Design Token Set**: The shared palette (primary/secondary/accent/neutral colors), type scale, spacing scale, and radii reused across the onboarding screens.
- **Onboarding Screen**: One of the three redesigned screens (Phone Entry, OTP Entry, Profile Setup), each consuming the shared Design Token Set.
- **Motion Motif**: The car/ride-themed animation asset(s) and their idle vs. success-transition states.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time viewer (e.g., a sponsor) rates the onboarding flow's visual polish as "premium/production-ready" rather than "prototype-looking" in an informal walkthrough.
- **SC-002**: A user can complete phone entry → OTP verification → profile setup in under 60 seconds with no confusion about where to tap or type.
- **SC-003**: 100% of interactive elements (input fields, buttons) remain fully usable even when animations are disabled or fail to render.
- **SC-004**: The redesigned flow introduces zero regressions to the previously verified working OTP request/confirm functionality (still testable end-to-end on the Android emulator).

## Assumptions

- "Premium" is interpreted as: cohesive branding, generous whitespace, smooth purposeful motion, clear typography hierarchy, and delightful micro-interactions — not a full custom illustration/animation studio production. A lightweight Lottie-style or React Native `Animated`/`Reanimated`-driven car animation satisfies the requirement; a hand-drawn/video-produced animation is out of scope for v1.
- No new backend changes are required for this feature; it is purely front-end visual/UX (reuses existing OTP request/confirm/profile APIs already working end-to-end).
- A single default brand palette (not user-selectable/themed) is sufficient for v1; dark mode is out of scope unless trivial to include via existing tokens.
- Target platform for verification/testing remains the existing Android emulator setup (iOS deferred per prior discussion).
- No new third-party paid design/animation service is required or introduced; any assets (icons, simple car graphic) are generated or hand-built, not purchased.
