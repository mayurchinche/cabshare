import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { CompositeScreenProps } from '@react-navigation/native';
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { LinearGradient } from 'expo-linear-gradient';

import { getAuthToken, getProfile, getStats, RiderProfileFull, setAuthToken } from '../services/apiClient';
import type { HomeTabParamList, RootStackParamList } from '../navigation/AppNavigator';
import Badge from '../components/Badge';
import Card from '../components/Card';
import { colors, gradients, spacing, typography } from '../theme';

type Props = CompositeScreenProps<
  BottomTabScreenProps<HomeTabParamList, 'ProfileTab'>,
  NativeStackScreenProps<RootStackParamList>
>;

const STATUS_LABEL: Record<RiderProfileFull['verification_status'], string> = {
  unverified: 'Not verified',
  pending: 'Pending',
  verified: 'Verified',
  rejected: 'Rejected',
};

const STATUS_BADGE: Record<RiderProfileFull['verification_status'], 'verified' | 'pending' | 'rejected'> = {
  unverified: 'pending',
  pending: 'pending',
  verified: 'verified',
  rejected: 'rejected',
};

/** Feature 004, page 16: view profile, KYC status, ride-history shortcut, logout. */
export default function ProfileAccountScreen({ navigation }: Props): React.JSX.Element {
  const [profile, setProfile] = useState<RiderProfileFull | null>(null);
  const [stats, setStats] = useState<{ rides_shared: number; total_saved: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const riderId = getAuthToken();
    if (!riderId) {
      setLoading(false);
      return;
    }
    getProfile(riderId)
      .then(setProfile)
      .finally(() => setLoading(false));
    getStats(riderId)
      .then(setStats)
      .catch(() => setStats({ rides_shared: 0, total_saved: 0 }));
  }, []);

  const onLogout = (): void => {
    setAuthToken('');
    navigation.getParent()?.reset({ index: 0, routes: [{ name: 'Verification' }] });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.centered} edges={['top']}>
        <ActivityIndicator color={colors.primary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.headerRow}>
        <LinearGradient colors={gradients.primary} style={styles.avatar}>
          <Text style={styles.avatarText}>{(profile?.display_name || '?').charAt(0)}</Text>
        </LinearGradient>
        <View>
          <Text style={typography.subheading}>{profile?.display_name ?? 'Rider'}</Text>
          {profile ? (
            <View style={styles.badgeWrap}>
              <Badge
                status={STATUS_BADGE[profile.verification_status]}
                label={STATUS_LABEL[profile.verification_status]}
              />
            </View>
          ) : null}
        </View>
      </View>

      <View style={styles.statsRow}>
        <Card style={styles.statCard}>
          <Text style={styles.statNumberTeal}>{stats?.rides_shared ?? 0}</Text>
          <Text style={typography.caption}>Rides</Text>
        </Card>
        <Card style={styles.statCard}>
          <Text style={styles.statNumber}>{profile?.rating?.toFixed(1) ?? '—'}</Text>
          <Text style={typography.caption}>Rating</Text>
        </Card>
      </View>

      <Card>
        <Pressable
          style={styles.listRow}
          onPress={() =>
            navigation.navigate('ProfileSetup', {
              riderId: getAuthToken() ?? '',
              mode: 'edit',
              initialName: profile?.display_name,
            })
          }
        >
          <Text style={typography.body}>Edit profile</Text>
          <Text style={typography.caption}>›</Text>
        </Pressable>
        <View style={styles.listRow}>
          <Text style={typography.body}>KYC status</Text>
          <Text style={typography.body}>{profile ? STATUS_LABEL[profile.verification_status] : '—'}</Text>
        </View>
        <Pressable style={styles.listRow} onPress={() => navigation.navigate('HistoryTab')}>
          <Text style={typography.body}>Ride history</Text>
          <Text style={typography.caption}>›</Text>
        </Pressable>
        <Pressable style={[styles.listRow, styles.listRowLast]} onPress={onLogout}>
          <Text style={[typography.body, { color: colors.error }]}>Log out</Text>
        </Pressable>
      </Card>
    </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  container: { padding: spacing.md },
  headerRow: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center', marginBottom: spacing.md },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: '#05060A', fontSize: 22, fontWeight: '800' },
  badgeWrap: { marginTop: spacing.xs },
  statsRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  statCard: { flex: 1, alignItems: 'center' },
  statNumber: { fontSize: 24, fontWeight: '800', color: colors.accent },
  statNumberTeal: { fontSize: 24, fontWeight: '800', color: colors.accentTeal },
  listRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm + 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  listRowLast: { borderBottomWidth: 0 },
});
