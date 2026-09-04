import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { LinearGradient } from 'expo-linear-gradient';

import { confirmMatch, declineMatch, getMatch, MatchDetail } from '../services/apiClient';
import type { RootStackParamList } from '../navigation/AppNavigator';
import Button from '../components/Button';
import Card from '../components/Card';
import { colors, gradients, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'MatchReview'>;

/**
 * FR-005/FR-006: show the masked partner profile, combined stop order, and itemized
 * distance-proportional fare-split, then let the rider confirm or decline. Per Constitution
 * Principle I, `MatchDetail.partner_profile` never carries phone/email — nothing here needs to
 * (or may) render contact info.
 *
 * Feature 002: restyled with shared theme/components — "Match found!" framing to make the
 * co-rider pairing feel like a positive, human moment rather than a plain data dump.
 */
export default function MatchReviewScreen({ route, navigation }: Props): React.JSX.Element {
  const { matchId } = route.params;
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getMatch(matchId)
      .then((data) => {
        if (!cancelled) setMatch(data);
      })
      .catch(() => Alert.alert('Error', 'Could not load match details.'))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [matchId]);

  const onConfirm = async (): Promise<void> => {
    setActing(true);
    try {
      const result = await confirmMatch(matchId);
      if (result.ride_id) {
        navigation.navigate('RideConfirm', { rideId: result.ride_id, matchId });
      } else {
        Alert.alert('Confirmed', 'Waiting for the other rider to confirm too.');
      }
    } catch {
      Alert.alert('Error', 'The confirmation window may have passed — please search again.');
    } finally {
      setActing(false);
    }
  };

  const onDecline = async (): Promise<void> => {
    setActing(true);
    try {
      await declineMatch(matchId);
      navigation.navigate('PostIntent');
    } catch {
      Alert.alert('Error', 'Could not decline this match.');
    } finally {
      setActing(false);
    }
  };

  if (loading || !match) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.flex}>
      <View style={styles.container}>
        <Text style={styles.headline}>🎉 Match found!</Text>

        <Card style={styles.card}>
          <View style={styles.partnerRow}>
            <LinearGradient colors={gradients.primary} style={styles.avatar}>
              <Text style={styles.avatarText}>{match.partner_profile.display_name.charAt(0)}</Text>
            </LinearGradient>
            <View>
              <Text style={typography.subheading}>{match.partner_profile.display_name}</Text>
              <Text style={typography.caption}>⭐ {match.partner_profile.rating.toFixed(1)} rating</Text>
            </View>
          </View>
        </Card>

        <Card style={styles.card}>
          <Text style={styles.sectionLabel}>Stops</Text>
          {match.combined_stop_order.map((stop, idx) => (
            <View
              key={idx}
              style={[styles.listRow, idx === match.combined_stop_order.length - 1 && styles.listRowLast]}
            >
              <Text style={typography.body}>
                {stop.rider_role === 'self' ? 'You' : 'Co-rider'}: {stop.stop_type} at {stop.location}
              </Text>
            </View>
          ))}
        </Card>

        <Card style={styles.card}>
          <Text style={styles.sectionLabel}>Fare split</Text>
          <Text style={typography.caption}>Total fare ₹{match.fare_split.total_fare.toFixed(2)}</Text>
          <Text style={styles.bigFare}>₹{match.fare_split.your_share.toFixed(2)}</Text>
          <Text style={typography.caption}>
            Your share · incl. ₹{match.fare_split.platform_fee_per_rider.toFixed(2)} platform fee
          </Text>
        </Card>
      </View>

      <View style={styles.actionBar}>
        {acting ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <>
            <Button title="Decline" variant="secondary" onPress={onDecline} style={styles.actionButton} />
            <Button title="Confirm" onPress={onConfirm} style={styles.actionButton} />
          </>
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
  container: { padding: spacing.md, gap: spacing.sm },
  headline: {
    ...typography.heading,
    marginBottom: spacing.sm,
  },
  card: { marginBottom: spacing.sm },
  partnerRow: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center' },
  avatar: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#05060A', fontWeight: '800', fontSize: 18 },
  listRow: {
    paddingVertical: spacing.xs + 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  listRowLast: { borderBottomWidth: 0 },
  bigFare: { fontSize: 32, fontWeight: '800', color: colors.accent, marginTop: spacing.xs },
  sectionLabel: {
    ...typography.caption,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
  },
  yourShare: { marginTop: spacing.xs, color: colors.success },
  actionBar: {
    flexDirection: 'row',
    gap: spacing.sm,
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
  },
  actionButton: { flex: 1 },
});
