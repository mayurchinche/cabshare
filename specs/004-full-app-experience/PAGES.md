# CabShare — Full App Page Inventory (Feature 004)

Goal: evolve from a 2-screen prototype into a complete, premium, end-to-end rider app.
Visual bar: CRED / INDMoney-tier polish (dark, confident, glassmorphism, bold numerics,
micro-animation) — not just "clean forms".

Every page below is a **real, permanent** screen (no placeholders). Pages reuse the Feature 002
design system (`mobile/src/theme`) and the Feature 002 shared components, extended per
`DESIGN-SYSTEM-V2.md`.

## Navigation map

```
Splash
  └─▶ PhoneEntry ──▶ OtpVerify ──▶ PanKyc ──▶ ProfileSetup ──▶ Home
                         └───────────────────────(returning rider, KYC already done)──▶ Home

Home (tab bar: Home | History | Profile)
  ├─▶ NewRideRequest ──▶ StationTrainPicker ──▶ TrainLiveStatus ──▶ Searching(Matching)
  │                                                                     ├─▶ MatchFound ──▶ RideTracking ──▶ RideCancel
  │                                                                     └─▶ NoMatch(EmptyState) ──▶ NewRideRequest
  ├─▶ RideHistoryList ──▶ RideHistoryDetail
  └─▶ ProfileAccount ──▶ PanKyc (re-verify / status)
```

## Page list (15)

| # | Page | Route | Purpose | Key premium elements |
|---|------|-------|---------|----------------------|
| 1 | Splash | `Splash` | Brand load, auth-token check | Full-bleed gradient, logo mark animation |
| 2 | Phone Entry | `PhoneEntry` (was `Verification` step 1) | Phone capture, start OTP | Gradient hero, CarMotion idle |
| 3 | OTP Verify | `OtpVerify` (was step 2) | 6-digit code confirm | Segmented input, CarMotion success |
| 4 | PAN / KYC Verify | `PanKyc` **(new)** | Capture + verify PAN for identity trust | Encrypted-badge UI, masked input, status timeline (Pending→Verified) |
| 5 | Profile Setup | `ProfileSetup` (was step 3) | Display name, photo, gender | Avatar picker, progress stepper |
| 6 | Home / Dashboard | `Home` **(new)** | Central hub post-login | Greeting hero, "Post a ride" CTA card, live active-ride card, quick stats (rides taken, ₹ saved) |
| 7 | New Ride Request | `NewRideRequest` (revamped `PostIntent`) | Capture ride intent | Station-to-station route card, luggage/gender chip selectors |
| 8 | Station & Train Picker | `StationTrainPicker` **(new, Feature 003)** | Pick origin/destination station, pick train | Autocomplete list, train card w/ scheduled time |
| 9 | Train Live Status | `TrainLiveStatus` **(new, Feature 003)** | Show real-time running status of chosen train | Progress rail (station-by-station), ETA badge, delay chip |
| 10 | Searching / Matching | `Searching` (revamped waiting state) | Waiting for a co-rider | CarMotion "searching" loop, radius/time countdown |
| 11 | Match Found | `MatchFound` (was `MatchReview`) | Review co-rider + fare split, confirm/decline | Partner card w/ rating, fare-split breakdown, confirm CTA |
| 12 | Ride Tracking | `RideTracking` (merged `RideConfirm` + live status) | Track both riders' trains converging → prompt cab booking at the right moment | Dual-train convergence rail, auto-prompt banner ("Both arriving in 6 min — book now"), deep-link buttons |
| 13 | Ride Cancel | `RideCancel` (was `Cancel`) | Cancel with fee transparency | Fee breakdown card |
| 14 | Ride History List | `RideHistoryList` **(new)** | Past rides | Timeline list, per-ride fare + co-rider chip |
| 15 | Ride History Detail | `RideHistoryDetail` **(new)** | Single past ride | Route recap, fare receipt, co-rider (masked), re-book CTA |
| 16 | Profile / Account | `ProfileAccount` **(new)** | View/edit profile, KYC status, logout | Verified badge, stats, settings list |

(16 screens total — table numbering above has a historical off-by-one, kept for traceability.)

## Explicit scope additions driving new pages

1. **PAN/KYC verification** — new `PanKyc` page + backend verification flow; PAN stored
   **encrypted at rest** (see `DATABASE.md` §KycDocument).
2. **Ride history** — `RideHistoryList` + `RideHistoryDetail`, backed by existing `rides`/`matches`
   tables (no new ride data model needed — it's a query, not a new entity).
3. **Live train tracking → auto cab-booking prompt** — `RideTracking` page and a new backend job
   (`auto_booking_prompt_job.py`, mirrors existing `matching_window_job.py`) that watches both
   riders' `TrainLiveStatusCache` rows and flips a ride into "prompt to book" once both are
   within a configurable ETA-to-common-station threshold.
4. **Home dashboard** — a real landing hub instead of dropping straight into a form.
5. **Profile/Account** — settings, KYC status, logout — table-stakes for any real app, currently
   completely missing.

## Explicitly out of scope for v1 (YAGNI — do not build)

- In-app chat / calling between riders (Constitution Principle I: no contact exchange at all).
- Payments / wallet (Constitution Principle V: flat fee only, no in-app money movement).
- Push notification preferences screen (single default channel is enough for MVP).
- Multi-language / i18n.
