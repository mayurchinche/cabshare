import React, { useCallback, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import type { CompositeScreenProps } from '@react-navigation/native';
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { getRideHistory, RideHistoryItem } from '../services/apiClient';
import type { HomeTabParamList, RootStackParamList } from '../navigation/AppNavigator';
import Card from '../components/Card';
import EmptyState from '../components/EmptyState';
import { colors, spacing, typography } from '../theme';

type Props = CompositeScreenProps<
  BottomTabScreenProps<HomeTabParamList, 'HistoryTab'>,
  NativeStackScreenProps<RootStackParamList>
>;

/** Feature 004, page 14: past rides — a read-only query over rides/matches/ride_intents (no
 * new DB table, see DATABASE.md). Refetches on focus so returning from a just-completed ride
 * shows it. Includes requests that never matched (open/expired/cancelled), not just booked
 * rides — every ride request is a transaction worth showing. */
export function historyStatusLabel(status: string): string {
  switch (status) {
    case 'open':
      return 'Still searching…';
    case 'expired':
      return 'No match found';
    case 'cancelled':
      return 'Cancelled';
    case 'matched':
      return 'Matched — booking pending';
    case 'ready':
      return 'Ready to book';
    case 'booked':
      return 'Booked';
    case 'in_progress':
      return 'In progress';
    case 'completed':
      return 'Completed';
    default:
      return status;
  }
}

export function statusBadgeColor(status: string): string {
  switch (status) {
    case 'completed':
      return colors.success;
    case 'cancelled':
    case 'expired':
      return colors.error;
    case 'in_progress':
    case 'booked':
      return colors.accent;
    default:
      return colors.textSecondary;
  }
}

export default function RideHistoryListScreen({ navigation }: Props): React.JSX.Element {
  const [rides, setRides] = useState<RideHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      setLoading(true);
      getRideHistory()
        .then((data) => {
          if (!cancelled) setRides(data);
        })
        .catch(() => {
          if (!cancelled) setRides([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
      return () => {
        cancelled = true;
      };
    }, [])
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.centered} edges={['top']}>
        <ActivityIndicator color={colors.primary} />
      </SafeAreaView>
    );
  }

  if (rides.length === 0) {
    return (
      <SafeAreaView style={styles.flex} edges={['top']}>
        <EmptyState title="No rides yet" description="Your completed rides will show up here." />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
    <FlatList
      style={styles.flex}
      contentContainerStyle={styles.container}
      data={rides}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => (
        <Card
          style={styles.card}
          onPress={() => navigation.getParent()?.navigate('RideHistoryDetail', { rideId: item.id })}
        >
          <View style={styles.row}>
            <View style={styles.flexShrink}>
              <Text style={typography.subheading}>
                {item.origin_station} → {item.destination}
              </Text>
              {item.partner_display_name ? (
                <Text style={typography.caption}>with {item.partner_display_name}</Text>
              ) : null}
              {/* Item 6: status is always shown, not just when there's no partner name, so
                  every request's current state (in-progress/completed/cancelled/etc.) is clear
                  at a glance. */}
              <Text style={[typography.caption, { color: statusBadgeColor(item.status) }]}>
                {historyStatusLabel(item.status)}
              </Text>
            </View>
            <Text style={styles.fare}>{item.your_share ? `₹${item.your_share.toFixed(0)}` : '—'}</Text>
          </View>
        </Card>
      )}
    />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  container: { padding: spacing.md },
  card: { marginBottom: spacing.sm },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  flexShrink: { flexShrink: 1, marginRight: spacing.sm },
  fare: { ...typography.subheading, color: colors.accent },
});
