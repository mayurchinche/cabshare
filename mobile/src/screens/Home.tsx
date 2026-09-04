import React, { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import type { CompositeScreenProps } from '@react-navigation/native';
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { HomeTabParamList, RootStackParamList } from '../navigation/AppNavigator';
import { ActiveActivity, getActiveActivity, getAuthToken, getStats } from '../services/apiClient';
import Button from '../components/Button';
import Card from '../components/Card';
import GradientCard from '../components/GradientCard';
import { colors, spacing, typography } from '../theme';

type Props = CompositeScreenProps<
  BottomTabScreenProps<HomeTabParamList, 'HomeTab'>,
  NativeStackScreenProps<RootStackParamList>
>;

/**
 * Feature 004, page 06: the central hub every rider lands on after login instead of dropping
 * straight into a form. Stats come from `GET /riders/{id}/stats` (real ride count + lifetime
 * savings). `active-activity` lets a rider resume a pending match/ride (or lets a pre-seeded
 * demo rider jump straight into MatchReview) without depending on in-memory nav params.
 */
function rideStatusLabel(status: string | null): string {
  switch (status) {
    case 'booked':
      return 'Cab booked';
    case 'in_progress':
      return 'Ride in progress';
    case 'completed':
      return 'Ride completed';
    default:
      return 'Awaiting cab booking';
  }
}

export default function HomeScreen({ navigation }: Props): React.JSX.Element {
  const [stats, setStats] = useState<{ rides_shared: number; total_saved: number } | null>(null);
  const [activity, setActivity] = useState<ActiveActivity | null>(null);

  useFocusEffect(
    useCallback(() => {
      const riderId = getAuthToken();
      if (!riderId) return;
      getStats(riderId)
        .then(setStats)
        .catch(() => setStats({ rides_shared: 0, total_saved: 0 }));
      getActiveActivity(riderId)
        .then(setActivity)
        .catch(() => setActivity(null));
    }, [])
  );

  const hasRides = !!stats && stats.rides_shared > 0;

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
    <ScrollView contentContainerStyle={styles.container}>
      <GradientCard>
        <Text style={styles.heroTitle}>Hey there 👋</Text>
        <Text style={styles.heroSubtitle}>Ready for your next shared ride?</Text>
      </GradientCard>

      {activity?.ride_id && (
        <Card style={styles.activityCard}>
          <Text style={styles.activityLabel}>Active ride</Text>
          <Text style={styles.activityTitle}>
            {activity.route_origin && activity.route_destination
              ? `${activity.route_origin} → ${activity.route_destination}`
              : `Your booking is ${activity.ride_status}`}
          </Text>
          {activity.co_rider_name && (
            <Text style={styles.activitySubtitle}>
              Matched with {activity.co_rider_name} · {rideStatusLabel(activity.ride_status)}
            </Text>
          )}
          {activity.progress_percent != null && (
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${activity.progress_percent}%` }]} />
            </View>
          )}
          <Button
            title="View ride"
            onPress={() => navigation.navigate('RideConfirm', { rideId: activity.ride_id!, matchId: activity.match_id! })}
            variant="secondary"
            style={styles.activityButton}
          />
        </Card>
      )}
      {!activity?.ride_id && activity?.match_id && activity.match_status === 'proposed' && (
        <Card style={styles.activityCard}>
          <Text style={styles.activityLabel}>Match found</Text>
          <Text style={styles.activityTitle}>A co-rider is waiting for your confirmation</Text>
          <Button
            title="Review match"
            onPress={() => navigation.navigate('MatchReview', { matchId: activity.match_id! })}
            variant="gold"
            style={styles.activityButton}
          />
        </Card>
      )}
      {!activity?.ride_id && !activity?.match_id && activity?.intent_status === 'open' && (
        <Card style={styles.activityCard}>
          <Text style={styles.activityLabel}>Searching</Text>
          <Text style={styles.activityTitle}>Looking for a co-rider on your route…</Text>
        </Card>
      )}

      <GradientCard style={styles.ctaCard}>
        <Text style={styles.ctaLabel}>Post a ride</Text>
        <Text style={styles.ctaTitle}>Find a co-rider now</Text>
        <Button
          title="+ New request"
          onPress={() => navigation.navigate('PostIntent')}
          variant="secondary"
          style={styles.ctaButton}
        />
      </GradientCard>

      {hasRides ? (
        <View style={styles.statsRow}>
          <Card style={styles.statCard}>
            <Text style={styles.statNumberTeal}>{stats!.rides_shared}</Text>
            <Text style={typography.caption}>Rides shared</Text>
          </Card>
          <Card style={styles.statCard}>
            <Text style={styles.statNumberGold}>₹{stats!.total_saved.toFixed(0)}</Text>
            <Text style={typography.caption}>Saved so far</Text>
          </Card>
        </View>
      ) : (
        stats && (
          <Card style={styles.emptyStatsCard}>
            <Text style={styles.emptyStatsTitle}>No rides yet</Text>
            <Text style={styles.emptyStatsSubtitle}>
              Post your first ride request to start sharing cabs and saving money.
            </Text>
          </Card>
        )
      )}
    </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { padding: spacing.md },
  heroTitle: { fontSize: 22, fontWeight: '700', color: colors.textPrimary },
  heroSubtitle: { fontSize: 13, color: 'rgba(245,246,250,0.85)', marginTop: spacing.xs },
  ctaCard: { marginBottom: spacing.md },
  ctaLabel: { fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.6, color: 'rgba(5,6,10,0.6)', marginBottom: spacing.xs },
  ctaTitle: { fontSize: 17, fontWeight: '700', color: '#05060A', marginBottom: spacing.sm },
  ctaButton: { marginTop: 0, backgroundColor: '#05060A', borderColor: 'transparent' },
  statsRow: { flexDirection: 'row', gap: spacing.sm },
  statCard: { flex: 1, alignItems: 'center' },
  statNumberTeal: { fontSize: 28, fontWeight: '800', color: colors.accentTeal },
  statNumberGold: { fontSize: 28, fontWeight: '800', color: colors.accent },
  activityCard: { marginBottom: spacing.md },
  activityLabel: { fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.6, color: colors.accentTeal, marginBottom: spacing.xs },
  activityTitle: { fontSize: 15, fontWeight: '700', color: colors.textPrimary, marginBottom: spacing.sm },
  activityButton: { marginTop: 0 },
  activitySubtitle: { fontSize: 12, color: colors.textSecondary, marginBottom: spacing.sm },
  progressTrack: { height: 4, borderRadius: 2, backgroundColor: 'rgba(245,246,250,0.12)', marginBottom: spacing.sm, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 2, backgroundColor: colors.accentTeal },
  emptyStatsCard: { alignItems: 'center', paddingVertical: spacing.lg },
  emptyStatsTitle: { fontSize: 15, fontWeight: '700', color: colors.textPrimary, marginBottom: spacing.xs },
  emptyStatsSubtitle: { fontSize: 12, color: colors.textSecondary, textAlign: 'center' },
});
