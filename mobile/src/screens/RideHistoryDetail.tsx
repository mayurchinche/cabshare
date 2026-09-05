import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { LinearGradient } from 'expo-linear-gradient';

import { getRideHistory, RideHistoryItem } from '../services/apiClient';
import { historyStatusLabel, statusBadgeColor } from './RideHistoryList';
import type { RootStackParamList } from '../navigation/AppNavigator';
import Button from '../components/Button';
import Card from '../components/Card';
import { colors, gradients, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'RideHistoryDetail'>;

/** Feature 004, page 15: single past ride — fare receipt + masked co-rider recap.
 * ponytail: reuses the list endpoint and finds the one ride client-side rather than adding a
 * `GET /rides/{id}/history` endpoint — the list is already small (one rider's own rides). */
export default function RideHistoryDetailScreen({ route, navigation }: Props): React.JSX.Element {
  const { rideId } = route.params;
  const [ride, setRide] = useState<RideHistoryItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getRideHistory()
      .then((rides) => {
        if (!cancelled) setRide(rides.find((r) => r.id === rideId) ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [rideId]);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (!ride) {
    return (
      <View style={styles.centered}>
        <Text style={typography.body}>Ride not found.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={typography.heading}>
        {ride.origin_station} → {ride.destination}
      </Text>
      <Text style={[typography.caption, styles.subtitle]}>
        {new Date(ride.created_at).toLocaleString()} ·{' '}
        <Text style={{ color: statusBadgeColor(ride.status) }}>{historyStatusLabel(ride.status)}</Text>
      </Text>

      <Card style={styles.card}>
        {ride.partner_display_name ? (
          <View style={styles.partnerRow}>
            <LinearGradient colors={gradients.primary} style={styles.avatar}>
              <Text style={styles.avatarText}>{ride.partner_display_name.charAt(0)}</Text>
            </LinearGradient>
            <View>
              <Text style={typography.subheading}>{ride.partner_display_name}</Text>
              <Text style={typography.caption}>⭐ {(ride.partner_rating ?? 0).toFixed(1)}</Text>
            </View>
          </View>
        ) : (
          <Text style={typography.body}>
            {ride.status === 'open' ? 'Still looking for a co-rider…' : 'No co-rider was found for this request.'}
          </Text>
        )}
      </Card>

      {ride.total_fare > 0 && (
      <Card style={styles.card}>
        <Text style={styles.sectionLabel}>Fare receipt</Text>
        <View style={styles.receiptRow}>
          <Text style={typography.body}>Total fare</Text>
          <Text style={typography.body}>₹{ride.total_fare.toFixed(2)}</Text>
        </View>
        <View style={styles.receiptRow}>
          <Text style={typography.body}>Platform fee</Text>
          <Text style={typography.body}>₹{ride.platform_fee.toFixed(2)}</Text>
        </View>
        <View style={styles.receiptRow}>
          <Text style={typography.subheading}>Your share</Text>
          <Text style={[typography.subheading, { color: colors.accent }]}>
            ₹{ride.your_share.toFixed(2)}
          </Text>
        </View>
      </Card>
      )}

      <Button title="Book this route again" onPress={() => navigation.navigate('PostIntent')} />
    </View>
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  container: { flex: 1, padding: spacing.md, backgroundColor: colors.background },
  subtitle: { marginTop: spacing.xs, marginBottom: spacing.md },
  card: { marginBottom: spacing.md },
  partnerRow: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center' },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: '#05060A', fontWeight: '800', fontSize: 18 },
  sectionLabel: { ...typography.caption, marginBottom: spacing.xs, textTransform: 'uppercase' },
  receiptRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.xs },
});
