import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../navigation/AppNavigator';
import { searchTrains, TrainSearchResult } from '../services/apiClient';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'TrainPicker'>;

/**
 * Feature 003, User Story 2: real train-route search between the two stations already chosen
 * in `PostIntent`, backed by RailRadar (`api/src/services/train_data`). Picking a specific
 * train lets the app later show live status + pair riders travelling on the same service
 * (`match_reason=same_train`, per data-model.md).
 */
export default function TrainPickerScreen({ route, navigation }: Props): React.JSX.Element {
  const { fromCode, toCode, travelDate } = route.params;
  const [results, setResults] = useState<TrainSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErrored(false);
    searchTrains(fromCode, toCode, travelDate)
      .then((trains) => {
        if (!cancelled) setResults(trains);
      })
      .catch(() => {
        if (!cancelled) setErrored(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fromCode, toCode, travelDate]);

  const onSelect = (train: TrainSearchResult): void => {
    navigation.navigate({
      name: 'PostIntent',
      params: {
        selectedTrain: {
          number: train.train_number,
          name: train.train_name,
          destinationArrivalTime: train.to_stop.scheduled_arrival,
          dayOffset: train.to_stop.day - train.from_stop.day,
        },
        travelDate,
      },
      merge: true,
    });
  };

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <View style={styles.container}>
        <Text style={typography.heading}>Trains on this route</Text>
        <Text style={[typography.caption, styles.subtitle]}>
          {fromCode} → {toCode} · {travelDate}
        </Text>

        {loading ? <ActivityIndicator color={colors.accentTeal} style={styles.loader} /> : null}
        {errored && !loading ? (
          <Text style={[typography.caption, styles.empty]}>
            Couldn't load trains right now — you can still submit without picking one.
          </Text>
        ) : null}

        <Pressable style={styles.skipRow} onPress={() => navigation.goBack()}>
          <Text style={styles.trackLink}>Skip — continue without a train →</Text>
        </Pressable>

        <FlatList
          data={results}
          keyExtractor={(item) => item.train_number}
          renderItem={({ item }) => (
            <Pressable style={styles.row} onPress={() => onSelect(item)}>
              <View style={styles.rowHeader}>
                <Text style={styles.trainName}>{item.train_name}</Text>
                <Text style={styles.trainNumber}>#{item.train_number}</Text>
              </View>
              <View style={styles.timeRow}>
                <Text style={typography.caption}>
                  {item.from_stop.scheduled_departure ?? '—'} {item.from_stop.station_code}
                </Text>
                <Text style={[typography.caption, styles.arrow]}>→</Text>
                <Text style={typography.caption}>
                  {item.to_stop.scheduled_arrival ?? '—'} {item.to_stop.station_code}
                </Text>
              </View>
              {item.duration_minutes ? (
                <Text style={styles.duration}>
                  {Math.floor(item.duration_minutes / 60)}h {item.duration_minutes % 60}m ·{' '}
                  {item.distance_km?.toFixed(0)} km
                </Text>
              ) : null}
            </Pressable>
          )}
          ListEmptyComponent={
            !loading && !errored ? (
              <Text style={[typography.caption, styles.empty]}>No trains found for this route</Text>
            ) : null
          }
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { flex: 1, padding: spacing.md },
  subtitle: { marginTop: spacing.xs, marginBottom: spacing.md },
  loader: { marginVertical: spacing.md },
  row: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: spacing.sm + 2,
    marginBottom: spacing.sm,
  },
  rowHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.xs },
  trainName: { ...typography.body, fontWeight: '700', flexShrink: 1, marginRight: spacing.xs },
  trainNumber: { ...typography.caption, color: colors.accentTeal },
  timeRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  arrow: { color: colors.textTertiary },
  duration: { ...typography.caption, marginTop: spacing.xs, color: colors.textTertiary },
  empty: { textAlign: 'center', marginTop: spacing.lg },
  skipRow: { marginBottom: spacing.sm },
  trackLink: { ...typography.caption, color: colors.accentTeal, fontWeight: '600' },
});
