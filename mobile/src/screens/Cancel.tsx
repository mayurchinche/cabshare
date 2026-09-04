import React, { useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { cancelRide } from '../services/apiClient';
import type { RootStackParamList } from '../navigation/AppNavigator';
import Button from '../components/Button';
import Card from '../components/Card';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Cancel'>;

/**
 * T043: confirm cancellation, showing the fee (if any) from the API's authoritative
 * `within_free_cutoff`/`fee_charged` calculation (FR-008) before finalizing.
 *
 * Feature 002: restyled with shared theme/components.
 */
export default function CancelScreen({ route, navigation }: Props): React.JSX.Element {
  const { rideId } = route.params;
  const [cancelling, setCancelling] = useState(false);

  const onConfirmCancel = async (): Promise<void> => {
    setCancelling(true);
    try {
      const result = await cancelRide(rideId);
      const message = result.within_free_cutoff
        ? 'Cancelled — no fee charged.'
        : `Cancelled — a ₹${result.fee_charged.toFixed(2)} fee applies (inside the 10-minute cutoff).`;
      Alert.alert('Ride cancelled', message, [
        { text: 'OK', onPress: () => navigation.navigate('PostIntent') },
      ]);
    } catch {
      Alert.alert('Error', 'Could not cancel this ride. Please try again.');
    } finally {
      setCancelling(false);
    }
  };

  return (
    <View style={styles.container}>
      <Card>
        <Text style={typography.heading}>Cancel this shared ride?</Text>
        <Text style={[typography.body, styles.description]}>
          Cancelling before the 10-minute cutoff is free. Cancelling inside the cutoff window may
          incur a fee — you&apos;ll see the exact amount before it&apos;s finalized.
        </Text>
        {cancelling ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <View style={styles.actionRow}>
            <Button
              title="Keep ride"
              variant="secondary"
              onPress={() => navigation.goBack()}
              style={styles.actionButton}
            />
            <Button
              title="Cancel ride"
              variant="destructive"
              onPress={onConfirmCancel}
              style={styles.actionButton}
            />
          </View>
        )}
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: spacing.md, backgroundColor: colors.background, justifyContent: 'center' },
  description: { marginTop: spacing.sm, marginBottom: spacing.lg, color: colors.textSecondary },
  actionRow: { flexDirection: 'row', gap: spacing.sm },
  actionButton: { flex: 1 },
});
