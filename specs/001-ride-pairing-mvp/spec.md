# Feature Specification: Station-to-Destination Ride Pairing (MVP)

**Feature Branch**: `001-ride-pairing-mvp`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "App where a traveller arriving at a station (e.g. Pune via Garib Rath
Express) heading to a destination (e.g. Baner) can post a cab-share intent with their luggage and
ride details, get paired with another traveller heading the same way within a ~2km radius, have a
ride booked with both riders' stops added so the fare splits, and pay a flat ₹10 platform fee per
ride. Should reduce solo-travel boredom and cab cost, without exposing either rider's contact
details to the other."

## Clarifications

### Session 2026-08-31

- Q: How long should the system wait for a compatible match before telling the rider "no match
  found"? → A: Riders may post an intent well ahead of arrival (e.g., at 7am for a 9am train).
  Active matching runs for a 5-minute window starting at the rider's expected arrival time (not
  at intent-submission time); if no match is found in that window, the rider is notified and can
  manually trigger a re-search (with a visible loading state) or fall back to solo booking.

- Q: What size categories should riders pick from when describing their luggage? → A: None /
  Small / Medium / Large (e.g., no bag, cabin bag, one suitcase, multiple suitcases).
- Q: How close to the ride's start time can a rider cancel without being charged a penalty fee?
  → A: 10 minutes before ride start; cancellations inside that window may incur a fee shown to
  the rider before they confirm the cancellation.

- Q: Should fare-split be an equal 50/50 split or distance-proportional? → A: Distance-
  proportional — each rider pays based on the portion of the shared route attributable to their
  own stop, not a flat 50/50 split.
- Q: When 3+ compatible riders wait simultaneously, which two get paired first? → A: First-come-
  first-served — pair the two riders whose intents were posted earliest; no best-fit scoring in
  MVP.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Post a ride intent and get paired (Priority: P1)

A traveller who has just arrived at a station enters their drop-off destination, approximate
luggage size, and preferred departure window, then submits it as a ride-share intent. The system
finds another verified traveller with a compatible destination and departure window within the
matching radius and pairs them.

**Why this priority**: Without matching, there is no product — this is the core value loop
(shared ride discovery) that everything else depends on.

**Independent Test**: Can be fully tested by two verified test accounts posting compatible
intents from the same station within the matching window and confirming both receive a match
notification with a combined route and fare-split preview.

**Acceptance Scenarios**:

1. **Given** a verified traveller posts an intent for a destination and departure window, **When**
   another verified traveller posts a compatible intent (destination within radius, overlapping
   departure window) within the matching timeout, **Then** both are shown a match with masked
   profile (first name + last initial, photo, rating), combined route, and estimated fare-split.
2. **Given** a traveller posts an intent, **When** no compatible match is found within the
   matching timeout, **Then** the traveller is notified and offered the choice to keep waiting,
   extend the radius/window, or book solo.
3. **Given** two travellers are matched, **When** either declines the match, **Then** both return
   to the unmatched pool without being told who declined or why.

---

### User Story 2 - Review match and confirm shared ride (Priority: P2)

Once paired, both riders review the proposed route (their two stops), the fare-split estimate, and
each other's masked profile, then each independently confirms before the ride is booked.

**Why this priority**: Matching alone isn't useful without a clear, trusted confirmation step
where riders see exactly what they're agreeing to (route, cost, and who they're riding with)
before committing.

**Independent Test**: Can be tested by advancing two matched test accounts to the confirmation
screen and verifying the ride only moves to "booking" state after both confirm, and cancels if
either declines within the confirmation window.

**Acceptance Scenarios**:

1. **Given** a proposed match, **When** both riders confirm within the confirmation window,
   **Then** the ride moves to "ready to book" and each rider sees pickup/drop stop order and an
   itemized fare-split (not a single opaque total).
2. **Given** a proposed match, **When** one rider does not respond within the confirmation
   window, **Then** the match expires and both riders return to the unmatched pool.
3. **Given** a confirmed match, **When** the ride reaches "ready to book," **Then** neither
   rider's phone number, email, or exact address is shown to the other at any point.

---

### User Story 3 - Cancel a pairing before ride start (Priority: P3)

A rider who has been matched (or whose ride is booked but not yet started) can cancel the shared
arrangement up to a defined cutoff, with the system notifying the other rider and re-opening the
matching pool if needed.

**Why this priority**: Plans change (missed connections, luggage issues); a no-penalty, clear
cancellation path is what makes strangers comfortable opting into shared rides in the first
place, but it is not required to prove the core matching loop works.

**Independent Test**: Can be tested by cancelling a confirmed pairing before the cutoff and
verifying the other rider is notified and can rebook solo or re-enter matching, with no fee
charged to the cancelling rider before the cutoff.

**Acceptance Scenarios**:

1. **Given** a confirmed pairing before the cancellation cutoff, **When** one rider cancels,
   **Then** the other rider is notified immediately and offered rebook-solo or re-match options,
   and no platform fee is charged to the cancelling rider.
2. **Given** a pairing past the cancellation cutoff, **When** one rider attempts to cancel,
   **Then** the system explains the cutoff has passed and shows any applicable fee before the
   rider confirms cancellation.

---

### Edge Cases

- What happens when more than two compatible travellers are waiting at once? (MVP pairs exactly
  two riders per ride, strictly first-come-first-served by intent posting time; no best-fit
  scoring. Others remain in the pool for the next available pairing.)
- How does the system handle a rider whose destination is updated after being matched? (Treated
  as a cancellation of the existing match; rider re-enters intent flow with the new destination.)
- How does the system handle a rider who fails identity verification? (Cannot post or accept an
  intent until verification succeeds; shown a clear reason and retry path.)
- What happens if the paired ride's actual driver route deviates significantly from the planned
  stop order? (Out of scope for MVP — driver routing is the booking partner's responsibility;
  the app only records the intended stop order at booking time.)
- What happens when a rider's departure window passes with no match and no manual action? (Intent
  expires automatically and the rider is notified.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a verified traveller to submit a ride-share intent containing
  origin (station), destination, luggage size category, and departure time window.
- **FR-002**: System MUST match two intents only when their destinations are within the
  configured matching radius (default 2 km) of each other and their departure windows overlap.
- **FR-002a**: System MUST allow a rider to post an intent in advance of their expected arrival
  time, and MUST run active matching for a 5-minute window starting at the rider's expected
  arrival time (not at submission time).
- **FR-002b**: System MUST notify the rider if no match is found by the end of the 5-minute
  matching window, and MUST let the rider manually trigger a re-search (showing a loading state)
  or proceed to solo booking.
- **FR-003**: System MUST NOT reveal either matched rider's phone number, email, or exact home/
  work address to the other rider at any point in the flow.
- **FR-004**: System MUST show each matched rider a masked profile of the other (first name +
  last initial, photo, rating) before either rider is asked to confirm.
- **FR-005**: System MUST require both matched riders to independently confirm before a ride is
  marked "ready to book"; the ride MUST NOT auto-confirm from a single rider's action.
- **FR-006**: System MUST calculate and display an itemized fare-split (base fare plus each
  rider's distance-proportional share, based on the portion of the shared route attributable to
  their own stop — not a flat 50/50 split) to both riders before booking confirmation.
- **FR-007**: System MUST charge a flat ₹10 platform fee per rider per completed shared ride,
  shown to the rider before they confirm the match.
- **FR-008**: System MUST allow either matched rider to decline a proposed match or cancel a
  confirmed pairing free of charge up until 10 minutes before the ride's start time; cancellations
  inside that 10-minute window MAY incur a fee, shown to the rider before they confirm.
- **FR-009**: System MUST notify the other rider immediately when their pairing is cancelled or
  declined, without revealing who initiated it or why.
- **FR-010**: System MUST expire an unmatched or unconfirmed intent automatically once its
  departure window and matching timeout have both passed, and notify the rider.
- **FR-011**: System MUST require identity verification (phone number plus a photo/ID check)
  before a traveller can post or accept a ride-share intent.
- **FR-012**: System MUST allow a rider to filter potential matches by gender preference when
  set.
- **FR-013**: System MUST record the intended pickup/drop stop order for a matched ride at
  booking confirmation time, independent of how the underlying cab booking is fulfilled.

### Key Entities

- **Rider**: A verified traveller using the app; attributes include verified name, photo, rating,
  gender preference setting, and verification status. Contact details are never exposed to other
  riders.
- **Ride Intent**: A rider's request to share a ride; attributes include origin station,
  destination, luggage size category (None / Small / Medium / Large), departure time window, and
  status (open, matched, expired, cancelled).
- **Match**: A pairing of exactly two compatible ride intents; attributes include the two
  riders, combined stop order, fare-split breakdown, and status (proposed, confirmed, cancelled,
  expired).
- **Ride**: The bookable outcome of a confirmed match; attributes include stop order, fare-split,
  platform fee per rider, and booking status (ready, booked, in progress, completed, cancelled).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A traveller can post a ride-share intent in under 60 seconds from opening the app.
- **SC-002**: At least 50% of intents posted at a station with another compatible traveller
  active within the matching window result in a proposed match within 5 minutes.
- **SC-003**: 90% of matched riders can review the route, masked profile, and fare-split and
  confirm or decline within 2 minutes of being matched.
- **SC-004**: Zero instances of one rider's phone number, email, or exact address being shown to
  their matched rider, verified via audit of match/ride records.
- **SC-005**: 95% of riders who cancel before the cancellation cutoff are not charged a penalty
  fee.

## Assumptions

- MVP pairs exactly two riders per shared ride; larger group pooling (3+) is out of scope for
  this feature and may be considered later.
- The matching radius, departure-window overlap tolerance, and cancellation cutoff are
  configurable values (default 2 km radius) rather than fixed in this spec, consistent with the
  project constitution's requirement that matching parameters be externally tunable.
- Actual cab booking with the ride partner (e.g., Ola/Uber/Rapido) is fulfilled through whatever
  booking mechanism the platform supports at the time (see constitution's booking-abstraction
  principle); this spec only covers the pairing, confirmation, and fare-split experience up to
  the point a ride is "ready to book."
- Payment collection for the platform fee and fare-split uses a payment method the rider has
  already saved to their account; adding a payment method is assumed to be handled by a standard
  onboarding flow and is not re-specified here.
- Identity verification (phone OTP + photo/ID check) is a one-time onboarding step reused across
  all future ride intents, not repeated per intent.
