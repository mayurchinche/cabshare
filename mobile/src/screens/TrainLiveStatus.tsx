import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../navigation/AppNavigator';
import { getTrainLiveStatus, TrainLiveStatus } from '../services/apiClient';
import Button from '../components/Button';
import Card from '../components/Card';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'TrainLiveStatus'>;

const REFRESH_INTERVAL_MS = 60_000; // ponytail: RailRadar free tier is 1,000 req/month — poll
// gently (once a minute while the screen is open) rather than on every render/animation frame;
// backend's own 15-min cache absorbs repeat calls across different riders viewing the same train.

function delayTone(delayMinutes: number | null): { label: string; color: string } {
  if (delayMinutes === null) return { label: 'Delay unknown', color: colors.textTertiary };
  if (delayMinutes <= 0) return { label: 'On time', color: colors.success };
  if (delayMinutes <= 20) return { label: `Running ${delayMinutes} min late`, color: colors.warning };
  return { label: `Running ${delayMinutes} min late`, color: colors.error };
}

/**
 * Feature 003 / screen-gap-analysis #9 (Train Live Status): real-time position via RailRadar,
 * unblocked by the user-provided paid key. Shows a simple progress rail between the last-halted
 * and next-halt stations (`segment_progress` 0-1 from the provider) rather than a full route
 * map — matches the "convergence rail" visual language already used in RideConfirm/#12.
 */
export default function TrainLiveStatusScreen({ route }: Props): React.JSX.Element {
  const { trainNumber, trainName, travelDate } = route.params;
  const [status, setStatus] = useState<TrainLiveStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errored, setErrored] = useState(false);

  const load = useCallback(
    (isRefresh: boolean) => {
      if (isRefresh) setRefreshing(true);
      getTrainLiveStatus(trainNumber, travelDate)
        .then((s) => {
          setStatus(s);
          setErrored(false);
        })
        .catch(() => setErrored(true))
        .finally(() => {
          setLoading(false);
          setRefreshing(false);
        });
    },
    [trainNumber, travelDate]
  );

  useEffect(() => {
    load(false);
    const timer = setInterval(() => load(false), REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [load]);

  if (loading) {
    return (
      <SafeAreaView style={styles.centered} edges={['top']}>
        <ActivityIndicator color={colors.accentTeal} size="large" />
      </SafeAreaView>
    );
  }

  if (errored || !status) {
    return (
      <SafeAreaView style={styles.centered} edges={['top']}>
        <Text style={typography.body}>Couldn't load live status right now.</Text>
        <Button title="Retry" onPress={() => load(false)} variant="secondary" style={styles.retryButton} />
      </SafeAreaView>
    );
  }

  const tone = delayTone(status.delay_minutes);
  const progressPct = Math.round((status.segment_progress ?? 0) * 100);

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.accentTeal} />}
      >
        <Card>
          <Text style={typography.heading}>{trainName ?? status.train_number}</Text>
          <Text style={[typography.caption, styles.trainNumberLabel]}>
            #{status.train_number} · {status.travel_date}
          </Text>

          <View style={[styles.delayChip, { borderColor: tone.color }]}>
            <View style={[styles.delayDot, { backgroundColor: tone.color }]} />
            <Text style={[styles.delayText, { color: tone.color }]}>{tone.label}</Text>
          </View>

          <View style={styles.rail}>
            <View style={styles.railStation}>
              <View style={[styles.railDot, styles.railDotActive]} />
              <Text style={styles.railLabel} numberOfLines={2}>
                {status.last_station_name ?? '—'}
              </Text>
            </View>
            <View style={styles.railTrack}>
              <View style={[styles.railFill, { width: `${progressPct}%` }]} />
            </View>
            <View style={styles.railStation}>
              <View style={styles.railDot} />
              <Text style={styles.railLabel} numberOfLines={2}>
                {status.next_station_name ?? '—'}
              </Text>
            </View>
          </View>
          <Text style={[typography.caption, styles.progressLabel]}>
            {progressPct}% of the way to next halt
          </Text>

          {!status.is_fresh ? (
            <Text style={styles.staleNotice}>Showing last known status — reconnecting…</Text>
          ) : null}
        </Card>

        <Button title="Refresh now" onPress={() => load(true)} variant="secondary" style={styles.refreshButton} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  centered: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.md },
  container: { padding: spacing.md },
  trainNumberLabel: { marginTop: spacing.xs, marginBottom: spacing.md },
  delayChip: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    gap: spacing.xs,
    marginBottom: spacing.lg,
  },
  delayDot: { width: 8, height: 8, borderRadius: 4 },
  delayText: { fontSize: 13, fontWeight: '700' },
  rail: { flexDirection: 'row', alignItems: 'center' },
  railStation: { width: 90, alignItems: 'center', gap: spacing.xs },
  railDot: { width: 14, height: 14, borderRadius: 7, backgroundColor: colors.textTertiary, borderWidth: 2, borderColor: colors.border },
  railDotActive: { backgroundColor: colors.accentTeal, borderColor: colors.accentTeal },
  railLabel: { ...typography.caption, textAlign: 'center' },
  railTrack: { flex: 1, height: 4, backgroundColor: colors.border, borderRadius: 2, marginHorizontal: spacing.xs, overflow: 'hidden' },
  railFill: { height: '100%', backgroundColor: colors.accentTeal, borderRadius: 2 },
  progressLabel: { textAlign: 'center', marginTop: spacing.sm },
  staleNotice: { ...typography.caption, color: colors.warning, textAlign: 'center', marginTop: spacing.md },
  refreshButton: { marginTop: spacing.md },
  retryButton: { marginTop: spacing.sm },
});
