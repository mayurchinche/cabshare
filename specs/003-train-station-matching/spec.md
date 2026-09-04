# Feature Specification: Train/Station-Based Ride Matching

**Feature Branch**: `003-train-station-matching`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "On the page where user is filling the details, it should get options of locations using some stations APIs of India, then it can also get the trains running for that route and show the options for the same. Based on that, show the live status of that train. Then based on other users travelling through the same train (or any other train reaching the spot at the same time), pair those people and show as match found, and further link to booking the train based on the given destinations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pick locations as railway stations (Priority: P1)

When posting a ride intent, instead of typing a free-text address, the rider picks their pickup and destination from a searchable list of Indian railway stations (by name or nearby-to-current-location).

**Why this priority**: Station-based input is the foundation everything else (train search, matching) is built on — without it, no other story can function.

**Independent Test**: Open Post Ride Intent, type a partial station name in the pickup field, and confirm a list of matching stations appears and can be selected; repeat for destination.

**Acceptance Scenarios**:

1. **Given** the rider is on Post Ride Intent, **When** they type 3+ characters into the pickup field, **Then** a list of matching station names/codes appears within 1 second.
2. **Given** a list of station suggestions is shown, **When** the rider selects one, **Then** the field stores the station code (not just free text) and displays the station's full name.
3. **Given** the rider has not granted location permission or has no GPS fix, **When** they open the field, **Then** search-by-name still works without requiring location access.

---

### User Story 2 - See trains running on the chosen route (Priority: P1)

Once both pickup and destination stations are selected, the rider sees a list of trains that run that route, so they can pick which train they intend to take (or discover which trains exist if unsure).

**Why this priority**: This is the second building block — matching later depends on knowing which train(s) a rider is on.

**Independent Test**: Select two stations with known train service between them and confirm a train list appears with recognizable train names/numbers and scheduled departure/arrival times.

**Acceptance Scenarios**:

1. **Given** pickup and destination stations are both selected, **When** the app looks up trains, **Then** a list of trains running that route is shown with train number, name, and scheduled departure/arrival times.
2. **Given** no trains run directly between the two selected stations, **When** the lookup completes, **Then** the rider sees a clear "no direct trains found" message rather than an empty/blank list.
3. **Given** the train lookup service is temporarily unavailable, **When** the rider requests the list, **Then** they see a friendly retry-able error rather than the app appearing frozen or broken.

---

### User Story 3 - Live running status of the chosen train (Priority: P2)

After selecting a specific train, the rider can see that train's current live running status (on time / delayed by how much, last known station) to gauge accuracy of the pairing before committing.

**Why this priority**: Adds trust and situational awareness, but the app remains usable (matching can proceed on schedule alone) if this data is temporarily unavailable — hence P2, not P1.

**Independent Test**: Select a specific train that is currently running and confirm live status (delay/last station) is displayed; also test with a train/time where no live data exists.

**Acceptance Scenarios**:

1. **Given** a rider selects a specific train, **When** live status data is available, **Then** the app shows current delay (in minutes) and the train's last reported station with a timestamp.
2. **Given** live status data is unavailable or the upstream source fails, **When** the rider views the train, **Then** the app clearly labels the status as "unavailable" rather than showing stale data as if current, and the rider can still proceed with matching using scheduled times.
3. **Given** live status was fetched some time ago, **When** it is displayed, **Then** the display includes "as of [time]" so riders know it may be stale.

---

### User Story 4 - Match with co-passengers on the same or arriving train (Priority: P1)

Riders who are on the same train, or on different trains arriving at the same station around the same time, are shown to each other as a "match found," so they can coordinate onward travel together (e.g., sharing a cab from the station).

**Why this priority**: This is the core value proposition of the app — pairing travelers — and is the direct reason all the station/train lookup groundwork exists.

**Independent Test**: Simulate two rider accounts posting ride intents for the same train (or two trains arriving at the same destination station within a defined time window) and confirm both see each other as a match.

**Acceptance Scenarios**:

1. **Given** two riders post intents for the exact same train number and date, **When** matching runs, **Then** both riders see each other in their Match Review screen labeled "same train."
2. **Given** two riders are on different trains arriving at the same destination station within a configurable time window (e.g., 30 minutes), **When** matching runs, **Then** both riders see each other labeled "arriving around the same time."
3. **Given** a rider has no matches yet, **When** they check Match Review, **Then** they see a designed empty state explaining matching is still in progress, not a blank/broken screen.
4. **Given** a match is found, **When** the rider views it, **Then** they see enough info to decide (co-passenger's first name/initials, train, arrival time, route overlap) without exposing full contact details until both parties confirm.

---

### User Story 5 - Proceed to book the train (Priority: P3)

After deciding on a train (matched or not), the rider can proceed toward actually booking a seat on that train.

**Why this priority**: Valuable for completing the end-to-end journey, but the matching value (Stories 1-4) stands on its own even if booking is just a hand-off rather than a full in-app transaction — hence P3.

**Independent Test**: From a selected train, tap "Book," and confirm the rider is taken to a booking entry point (in-app or external) pre-filled with the chosen train, date, and stations.

**Acceptance Scenarios**:

1. **Given** a rider has selected a specific train, **When** they tap "Book this train," **Then** they are taken to a booking flow (in-app form or external booking site/app) with the train number, date, and station codes pre-filled.
2. **Given** no in-app booking/payment capability exists, **When** the rider reaches the booking step, **Then** the app clearly communicates that final booking/payment happens outside the app (e.g., via IRCTC), avoiding any implication that payment is handled in-app.

---

### Edge Cases

- What happens when a rider selects two stations with no rail connection at all? → Show "no direct trains" and suggest broadening search (e.g., nearby stations) rather than a dead end.
- What happens when the live-status data source is rate-limited or down for an extended period? → Feature must degrade to "schedule only" mode; matching must not be blocked by live-status unavailability.
- What happens if a matched co-passenger cancels their ride intent after a match was shown? → The other rider must be notified the match is no longer valid, not left believing a stale match is still active.
- What happens when a rider's train is delayed enough that the original "arriving same time" match window no longer holds? → Match window should be evaluated using best-available (live > scheduled) timing, and stale matches should be re-evaluated or flagged.
- What happens with duplicate/ambiguous station names (India has stations with similar names in different states)? → Station picker must disambiguate using station code and state/city, not name alone.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a searchable station picker (by partial name) for both pickup and destination fields when posting a ride intent.
- **FR-002**: System MUST resolve each selected location to a canonical station code, not free-text.
- **FR-003**: System MUST look up and display trains running between two selected stations, including train number, name, and scheduled departure/arrival times.
- **FR-004**: System MUST clearly indicate when no direct trains are found for a selected station pair.
- **FR-005**: System MUST attempt to fetch live running status (delay, last known station, as-of timestamp) for a rider's selected train, and MUST clearly label this data as unavailable/stale when the source fails or data is old, rather than failing silently.
- **FR-006**: System MUST NOT block ride-intent posting or matching on live-status availability — scheduled times are a sufficient fallback input to matching.
- **FR-007**: System MUST match riders who share the exact same train number and travel date as "same train" matches.
- **FR-008**: System MUST match riders on different trains whose arrival at a shared destination station falls within a configurable time window (default 30 minutes, using live status when available, scheduled time otherwise) as "similar arrival time" matches.
- **FR-009**: System MUST invalidate/re-flag a shown match if the underlying ride intent is cancelled or the timing assumption changes enough to break the match window.
- **FR-010**: System MUST present matches with enough information to decide (first name/initials, train, timing, route overlap) while withholding full contact details until mutual confirmation.
- **FR-011**: System MUST provide a "book this train" action that hands off to an external or in-app booking entry point with train number, date, and stations pre-filled, and MUST clearly disclose that no in-app payment/booking transaction occurs if none is implemented.
- **FR-012**: System MUST disambiguate stations with similar/duplicate names using station code plus state/city context.

### Key Entities

- **Station**: A canonical railway station with code, name, state/city, and coordinates, used for pickup/destination selection and disambiguation.
- **Train**: A scheduled train service with number, name, and route (ordered list of stations with scheduled times).
- **Train Live Status**: A point-in-time snapshot of a specific train's real-world running state (delay, last station, as-of timestamp), tied to a Train and a specific travel date.
- **Ride Intent** *(existing entity, extended)*: Now references a resolved Station for pickup/destination and, optionally, a specific selected Train.
- **Match** *(existing entity, extended)*: Now carries a match reason of either "same train" or "similar arrival time," plus the timing basis (live vs. scheduled) used to compute it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A rider can go from opening Post Ride Intent to seeing a train list for their chosen route in under 10 seconds of interaction.
- **SC-002**: At least 90% of station name searches return the intended station within the first 5 suggestions.
- **SC-003**: Riders on the same train are matched to each other within one matching cycle (e.g., a few minutes) of both posting intents, without manual intervention.
- **SC-004**: Live-status unavailability never prevents a rider from completing ride-intent posting or seeing matches — 0% hard-blocking failures attributable to the live-status source.
- **SC-005**: 100% of matches shown are re-validated (or clearly marked stale) if either party's ride intent is cancelled.

## Assumptions

- "Stations APIs of India" refers to freely available community/open station master data (e.g., station code/name/lat-lng datasets) plus best-effort unofficial train-search and live-status sources, since no official free real-time Indian Railways API exists; see accompanying research notes. The system is designed to degrade gracefully when these unofficial sources are rate-limited or unavailable.
- "Booking the train" means handing off to an external booking flow (e.g., IRCTC or a third-party ticketing site/deep link) pre-filled with route/train/date — full in-app seat booking and payment is out of scope for this feature, since no free public booking-transaction API exists.
- The existing pickup/destination free-text fields in the current Ride Intent flow are replaced/extended by the station picker described here; existing matching-by-geography logic (if any) is extended, not removed, so non-station-based matching can remain as a fallback where useful.
- A "configurable time window" for arrival-based matching defaults to 30 minutes and can be tuned later; exact value is not user-facing in v1.
- This feature depends on Feature 002 (premium UI) for its visual presentation but is independently functional/testable without it (i.e., it can ship with baseline styling first if needed).
