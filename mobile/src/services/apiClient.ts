/**
 * Minimal API client. Only POST /intents is queued when offline (a rider posting an intent
 * right off a train may briefly have no signal) — other calls fail fast, since they always
 * happen after the rider has connectivity again (reviewing/confirming a match).
 *
 * ponytail: in-memory + AsyncStorage-backed queue, single retry-on-reconnect listener; upgrade
 * to a full offline-sync library only if more endpoints need queuing later.
 */
import { Platform } from 'react-native';

// The Android emulator's "localhost" is its own loopback, not the host machine's — 10.0.2.2 is
// the documented alias back to the dev machine. iOS Simulator shares the host's network, so
// plain localhost works there. Real devices (incl. Expo Go) need EXPO_PUBLIC_API_BASE_URL set
// to the host's LAN IP — RN only inlines env vars prefixed EXPO_PUBLIC_ at build time.
const DEFAULT_BASE_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? DEFAULT_BASE_URL;

export interface RideIntentCreate {
  origin_station: string;
  origin_lat: number;
  origin_lng: number;
  destination: string;
  destination_lat: number;
  destination_lng: number;
  luggage_size: 'none' | 'small' | 'medium' | 'large';
  expected_arrival_time: string;
  gender_preference?: 'any' | 'male' | 'female' | null;
  selected_train_number?: string | null;
  travel_date?: string | null;
  final_destination?: string | null;
  final_destination_lat?: number | null;
  final_destination_lng?: number | null;
}

export interface RideIntent {
  id: string;
  status: 'open' | 'matched' | 'expired' | 'cancelled';
  matching_window_opens_at: string;
  matching_window_closes_at: string;
  match_id: string | null;
  selected_train_number?: string | null;
  travel_date?: string | null;
  final_destination?: string | null;
  final_destination_lat?: number | null;
  final_destination_lng?: number | null;
}

let authToken: string | null = null;

/** Stores the verified rider's own ID — sent as `X-Rider-Id` (MVP auth stand-in, matches
 * `api/src/api/deps.py`). Not persisted across app restarts yet (no AsyncStorage dependency
 * added for this MVP pass); re-verifying via OTP after a restart is the accepted gap. */
export function setAuthToken(riderId: string): void {
  authToken = riderId;
}

export function getAuthToken(): string | null {
  return authToken;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(authToken ? { 'X-Rider-Id': authToken } : {}),
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

const pendingIntentQueue: RideIntentCreate[] = [];

export async function createRideIntent(payload: RideIntentCreate): Promise<RideIntent> {
  try {
    return await request('/intents', { method: 'POST', body: JSON.stringify(payload) });
  } catch (err) {
    // Assume network failure means offline; queue for retry rather than losing the submission.
    pendingIntentQueue.push(payload);
    throw err;
  }
}

export async function flushPendingIntents(): Promise<void> {
  while (pendingIntentQueue.length > 0) {
    const next = pendingIntentQueue[0];
    await request('/intents', { method: 'POST', body: JSON.stringify(next) });
    pendingIntentQueue.shift();
  }
}

export function getPendingIntentCount(): number {
  return pendingIntentQueue.length;
}

export async function getRideIntent(intentId: string): Promise<RideIntent> {
  return request(`/intents/${intentId}`);
}

export async function retryMatching(intentId: string): Promise<void> {
  await request(`/intents/${intentId}/research`, { method: 'POST' });
}

export interface Station {
  id: string;
  station_code: string;
  name: string;
  state: string | null;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
}

export async function searchStations(query: string): Promise<Station[]> {
  if (query.trim().length < 2) return [];
  return request(`/stations/search?q=${encodeURIComponent(query.trim())}`);
}

export interface Place {
  display_name: string;
  latitude: number;
  longitude: number;
}

/** Real-world address/POI search (drop-off picker) — distinct from `searchStations`, which
 * only covers railway stations. Free OpenStreetMap Nominatim data, no API key. */
export async function searchPlaces(query: string): Promise<Place[]> {
  if (query.trim().length < 3) return [];
  return request(`/places/search?q=${encodeURIComponent(query.trim())}`);
}

export interface StopEntry {
  rider_role: 'self' | 'partner';
  stop_type: 'pickup' | 'drop';
  location: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface MaskedRiderProfile {
  display_name: string;
  photo_url: string | null;
  rating: number;
}

export interface MatchDetail {
  id: string;
  status: 'proposed' | 'confirmed' | 'cancelled' | 'expired';
  partner_profile: MaskedRiderProfile;
  combined_stop_order: StopEntry[];
  fare_split: {
    total_fare: number;
    platform_fee_per_rider: number;
    your_share: number;
    partner_share: number;
  };
  confirmation_deadline: string;
}

export interface ConfirmMatchResult {
  status: string;
  ride_id: string | null;
}

export interface CancellationResult {
  status: 'cancelled';
  fee_charged: number;
  within_free_cutoff: boolean;
}

export async function getMatch(matchId: string): Promise<MatchDetail> {
  return request(`/matches/${matchId}`);
}

export async function confirmMatch(matchId: string): Promise<ConfirmMatchResult> {
  return request(`/matches/${matchId}/confirm`, { method: 'POST' });
}

export async function declineMatch(matchId: string): Promise<unknown> {
  return request(`/matches/${matchId}/decline`, { method: 'POST' });
}

export async function cancelRide(rideId: string): Promise<CancellationResult> {
  return request(`/rides/${rideId}/cancel`, { method: 'POST' });
}

// Item 6: manual self-reported status advance (booked -> in_progress -> completed); cancellation
// stays on cancelRide() above since only that path runs the fee/cutoff logic.
export async function updateRideStatus(
  rideId: string,
  status: 'booked' | 'in_progress' | 'completed'
): Promise<{ id: string; status: string }> {
  return request(`/rides/${rideId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export interface OtpRequestResult {
  rider_id: string;
  debug_otp_code: string; // ponytail: dev-only stand-in until a real SMS provider is wired
}

export interface OtpConfirmResult {
  rider_id: string;
  needs_kyc: boolean;
  needs_profile: boolean;
}

export interface RiderProfile {
  id: string;
  display_name: string;
  verification_status: 'unverified' | 'pending' | 'verified' | 'rejected';
}

export interface RiderProfileFull extends RiderProfile {
  photo_url: string | null;
  rating: number;
}

export interface KycStatusResult {
  status: 'pending' | 'verified' | 'rejected';
  pan_number_last4: string;
  verified_at: string | null;
  rejection_reason: string | null;
}

export interface RideHistoryItem {
  id: string;
  origin_station: string;
  destination: string;
  status: string;
  partner_display_name: string | null;
  partner_rating: number | null;
  your_share: number;
  total_fare: number;
  platform_fee: number;
  created_at: string;
}

export async function requestOtp(phoneNumber: string): Promise<OtpRequestResult> {
  return request('/riders/otp/request', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber }),
  });
}

export async function confirmOtp(phoneNumber: string, code: string): Promise<OtpConfirmResult> {
  return request('/riders/otp/confirm', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, code }),
  });
}

export async function submitKyc(
  riderId: string,
  payload: { pan_number: string; name_on_document: string }
): Promise<KycStatusResult> {
  return request(`/riders/${riderId}/kyc`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function getKycStatus(riderId: string): Promise<KycStatusResult> {
  return request(`/riders/${riderId}/kyc`);
}

export async function getProfile(riderId: string): Promise<RiderProfileFull> {
  return request(`/riders/${riderId}`);
}

export interface RiderStats {
  rides_shared: number;
  total_saved: number;
}

export async function getRideHistory(): Promise<RideHistoryItem[]> {
  return request('/rides');
}

export async function getStats(riderId: string): Promise<RiderStats> {
  return request(`/riders/${riderId}/stats`);
}

export interface ActiveActivity {
  intent_id: string | null;
  intent_status: string | null;
  match_id: string | null;
  match_status: string | null;
  ride_id: string | null;
  ride_status: string | null;
  route_origin: string | null;
  route_destination: string | null;
  co_rider_name: string | null;
  progress_percent: number | null;
}

/** Home dashboard: lets the app resume a pending match/ride after a restart, or for a
 * pre-seeded demo rider, without depending on in-memory navigation params. */
export async function getActiveActivity(riderId: string): Promise<ActiveActivity> {
  return request(`/riders/${riderId}/active-activity`);
}

export async function submitProfile(
  riderId: string,
  profile: { display_name: string; gender: 'male' | 'female' | 'other' | 'undisclosed'; photo_url: string }
): Promise<RiderProfile> {
  return request(`/riders/${riderId}/profile`, { method: 'PATCH', body: JSON.stringify(profile) });
}

// ---- Feature 003: live train search + tracking (RailRadar-backed, see api/src/api/trains.py) ----

export interface TrainRouteStop {
  station_code: string;
  station_name: string;
  scheduled_arrival: string | null;
  scheduled_departure: string | null;
  sequence: number;
  day: number;
}

export interface TrainSearchResult {
  train_number: string;
  train_name: string;
  from_stop: TrainRouteStop;
  to_stop: TrainRouteStop;
  distance_km: number | null;
  duration_minutes: number | null;
}

export async function searchTrains(
  fromCode: string,
  toCode: string,
  travelDate?: string
): Promise<TrainSearchResult[]> {
  const params = new URLSearchParams({ from: fromCode, to: toCode });
  if (travelDate) params.set('travel_date', travelDate);
  return request(`/trains/search?${params.toString()}`);
}

export interface TrainLiveStatus {
  train_number: string;
  travel_date: string;
  status: string;
  delay_minutes: number | null;
  last_station_code: string | null;
  last_station_name: string | null;
  next_station_code: string | null;
  next_station_name: string | null;
  segment_progress: number | null;
  is_fresh: boolean;
}

export async function getTrainLiveStatus(
  trainNumber: string,
  travelDate: string
): Promise<TrainLiveStatus> {
  return request(`/trains/${encodeURIComponent(trainNumber)}/live?travel_date=${travelDate}`);
}
