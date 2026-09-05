import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Linking, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { getMatch, MatchDetail, updateRideStatus } from '../services/apiClient';
import type { RootStackParamList } from '../navigation/AppNavigator';
import Button from '../components/Button';
import Card from '../components/Card';
import CarMotion from '../components/CarMotion';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'RideConfirm'>;

// ponytail: MVP has no partner-API multi-stop booking (Constitution Principle IV /
// BookingProvider = manual_confirmation only) — no aggregator publicly exposes a shared/
// multi-stop booking API. So each rider deep-links their OWN single leg (shared arrival
// station → their own final destination) into whichever cab app they have, using each
// provider's documented universal-link params where coordinates are supported.
function buildCabDeepLink(
  name: string,
  pickup: { lat: number | null | undefined; lng: number | null | undefined; label: string } | null,
  dropoff: { lat: number | null | undefined; lng: number | null | undefined; label: string } | null
): string {
  const hasCoords =
    pickup?.lat != null && pickup?.lng != null && dropoff?.lat != null && dropoff?.lng != null;

  if (name === 'Uber') {
    if (!hasCoords) return 'uber://';
    const params = new URLSearchParams({
      action: 'setPickup',
      'pickup[latitude]': String(pickup!.lat),
      'pickup[longitude]': String(pickup!.lng),
      'pickup[nickname]': pickup!.label,
      'dropoff[latitude]': String(dropoff!.lat),
      'dropoff[longitude]': String(dropoff!.lng),
      'dropoff[nickname]': dropoff!.label,
    });
    return `uber://?${params.toString()}`;
  }
  if (name === 'Ola') {
    if (!hasCoords) return 'olacabs://';
    const params = new URLSearchParams({
      serviceType: 'p2p',
      lat: String(pickup!.lat),
      lng: String(pickup!.lng),
      drop_lat: String(dropoff!.lat),
      drop_lng: String(dropoff!.lng),
    });
    return `olacabs://app/launch?${params.toString()}`;
  }
  // Rapido has no documented public deep-link coordinate params — bare app open.
  return 'rapido://';
}

const CAB_APP_NAMES = ['Ola', 'Uber', 'Rapido'];

const MATCH_POLL_INTERVAL_MS = 10000;

/**
 * T038: "ready to book" state. Both riders have confirmed; the rider books the cab themselves
 * in their preferred app (stops shown here) and taps "I've booked" once done — there is no
 * backend "mark booked" call in this MVP's contract, so that action is local UI state only.
 *
 * T044: also polls the match while on this screen so that if the OTHER rider cancels
 * (`GET /matches/{id}` push-notification-fallback), this rider gets a rebook-solo / re-match
 * prompt instead of being left staring at stale "ready to book" details.
 *
 * Feature 002: restyled with shared theme/components + the success CarMotion state.
 */
export default function RideConfirmScreen({ route, navigation }: Props): React.JSX.Element {
  const { matchId, rideId } = route.params;
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [rideStatus, setRideStatus] = useState<'ready' | 'booked' | 'in_progress' | 'completed'>(
    'ready'
  );
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [partnerCancelled, setPartnerCancelled] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const poll = async (): Promise<void> => {
      try {
        const data = await getMatch(matchId);
        if (cancelled) return;
        setMatch(data);
        if (data.status === 'cancelled' && rideStatus !== 'completed') {
          setPartnerCancelled(true);
        }
      } catch {
        // ignore transient poll failures; next tick retries
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    poll();
    const timer = setInterval(poll, MATCH_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchId]);

  const selfPickup = match?.combined_stop_order.find(
    (s) => s.rider_role === 'self' && s.stop_type === 'pickup'
  );
  const selfDrop = match?.combined_stop_order.find(
    (s) => s.rider_role === 'self' && s.stop_type === 'drop'
  );

  const openCabApp = (name: string): void => {
    const url = buildCabDeepLink(
      name,
      selfPickup ? { lat: selfPickup.latitude, lng: selfPickup.longitude, label: selfPickup.location } : null,
      selfDrop ? { lat: selfDrop.latitude, lng: selfDrop.longitude, label: selfDrop.location } : null
    );
    Linking.openURL(url).catch(() =>
      Alert.alert('App not found', `Install ${name} to book directly from here.`)
    );
  };

  // Item 6: advance the ride's self-reported status; no live GPS/driver feed exists yet, so
  // riders manually mark progress (booked -> in_progress -> completed).
  const advanceStatus = async (next: 'booked' | 'in_progress' | 'completed'): Promise<void> => {
    setStatusUpdating(true);
    try {
      await updateRideStatus(rideId, next);
      setRideStatus(next);
    } catch {
      Alert.alert('Error', 'Could not update the ride status. Please try again.');
    } finally {
      setStatusUpdating(false);
    }
  };

  if (loading || !match) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (partnerCancelled) {
    return (
      <View style={styles.container}>
        <Card>
          <Text style={typography.subheading}>Your co-rider cancelled this shared ride.</Text>
          <Text style={[typography.body, styles.spaced]}>
            You can continue solo or search for a new co-rider.
          </Text>
          <View style={styles.actionRow}>
            <Button
              title="Search again"
              variant="secondary"
              onPress={() => navigation.navigate('PostIntent')}
              style={styles.actionButton}
            />
            <Button
              title="Continue solo"
              onPress={() => setPartnerCancelled(false)}
              style={styles.actionButton}
            />
          </View>
        </Card>
      </View>
    );
  }

  return (
    <View style={styles.flex}>
      <View style={styles.container}>
        <CarMotion state="success" caption="Ride ready — time to book" />

        <Card style={styles.card}>
          <Text style={styles.sectionLabel}>Stops</Text>
          {match.combined_stop_order.map((stop, idx) => (
            <Text key={idx} style={typography.body}>
              {stop.rider_role === 'self' ? 'You' : 'Co-rider'}: {stop.stop_type} at {stop.location}
            </Text>
          ))}
          <Text style={[typography.subheading, styles.yourShare]}>
            Your share: ₹{match.fare_split.your_share.toFixed(2)}
          </Text>
        </Card>

        <Card style={styles.card}>
          <Text style={styles.sectionLabel}>Book with</Text>
          <View style={styles.actionRow}>
            {CAB_APP_NAMES.map((name) => (
              <Button
                key={name}
                title={name}
                variant="secondary"
                onPress={() => openCabApp(name)}
                style={styles.actionButton}
              />
            ))}
          </View>
        </Card>
      </View>

      <View style={styles.actionBar}>
        {rideStatus === 'completed' ? (
          <Text style={styles.bookedText}>Ride completed — hope it went smoothly! 🚕</Text>
        ) : rideStatus === 'ready' ? (
          <>
            <Button
              title="Cancel ride"
              variant="destructive"
              onPress={() => navigation.navigate('Cancel', { rideId })}
              style={styles.actionButton}
            />
            <Button
              title="I've booked the cab"
              variant="gold"
              loading={statusUpdating}
              onPress={() => advanceStatus('booked')}
              style={styles.actionButton}
            />
          </>
        ) : rideStatus === 'booked' ? (
          <>
            <Button
              title="Cancel ride"
              variant="destructive"
              onPress={() => navigation.navigate('Cancel', { rideId })}
              style={styles.actionButton}
            />
            <Button
              title="Mark ride started"
              variant="gold"
              loading={statusUpdating}
              onPress={() => advanceStatus('in_progress')}
              style={styles.actionButton}
            />
          </>
        ) : (
          <Button
            title="Mark ride completed"
            variant="gold"
            loading={statusUpdating}
            onPress={() => advanceStatus('completed')}
            style={styles.actionButton}
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  container: { flex: 1, padding: spacing.md },
  card: { marginTop: spacing.sm },
  sectionLabel: {
    ...typography.caption,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
  },
  yourShare: { marginTop: spacing.sm, color: colors.success },
  actionRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xs },
  actionButton: { flex: 1 },
  spaced: { marginTop: spacing.xs, marginBottom: spacing.md },
  actionBar: {
    flexDirection: 'row',
    gap: spacing.sm,
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
  },
  bookedText: {
    ...typography.subheading,
    color: colors.success,
    textAlign: 'center',
    flex: 1,
  },
});
