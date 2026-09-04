import React, { useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../navigation/AppNavigator';
import { submitKyc } from '../services/apiClient';
import Button from '../components/Button';
import Card from '../components/Card';
import TextField from '../components/TextField';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'PanKyc'>;

const PAN_REGEX = /^[A-Z]{5}[0-9]{4}[A-Z]$/;

/**
 * Feature 004, page 04: one-time PAN verification so every rider on the platform is
 * accountable (identity trust), before they can post/accept a ride. PAN is encrypted at rest
 * server-side (`api/src/services/encryption.py`) — this screen never persists it locally beyond
 * the in-flight form state, and never displays it back once submitted (only the masked last-4
 * from the server response).
 */
export default function PanKycScreen({ route, navigation }: Props): React.JSX.Element {
  const { riderId } = route.params;
  const [panNumber, setPanNumber] = useState('');
  const [nameOnDocument, setNameOnDocument] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  const onSubmit = async (): Promise<void> => {
    const normalized = panNumber.trim().toUpperCase();
    if (!PAN_REGEX.test(normalized)) {
      setError('Enter a valid 10-character PAN (e.g. ABCDE1234F).');
      return;
    }
    if (!nameOnDocument.trim()) {
      setError('Enter the name exactly as it appears on your PAN card.');
      return;
    }
    setError(undefined);
    setSubmitting(true);
    try {
      await submitKyc(riderId, { pan_number: normalized, name_on_document: nameOnDocument.trim() });
      navigation.navigate('ProfileSetup', { riderId });
    } catch {
      Alert.alert('Error', 'Could not submit your PAN for verification. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container}>
      <Text style={typography.heading}>Verify your identity</Text>
      <Text style={[typography.caption, styles.subtitle]}>
        One-time PAN check keeps every rider on CabShare accountable
      </Text>

      <Card style={styles.lockCard}>
        <Text style={typography.caption}>🔒 Encrypted end-to-end · never shown to co-riders</Text>
      </Card>

      <Card>
        <TextField
          label="PAN number"
          value={panNumber}
          onChangeText={(t) => setPanNumber(t.toUpperCase())}
          placeholder="ABCDE1234F"
          autoCapitalize="characters"
          maxLength={10}
          errorText={error}
        />
        <TextField
          label="Name as on PAN"
          value={nameOnDocument}
          onChangeText={setNameOnDocument}
          placeholder="Full name"
        />
        <Button title="Submit for verification" onPress={onSubmit} loading={submitting} />
      </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { padding: spacing.md },
  subtitle: { marginTop: spacing.xs, marginBottom: spacing.md },
  lockCard: { marginBottom: spacing.md },
});
