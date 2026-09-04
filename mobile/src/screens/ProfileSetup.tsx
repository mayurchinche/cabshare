import React, { useState } from 'react';
import { Alert, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../navigation/AppNavigator';
import { setAuthToken, submitProfile } from '../services/apiClient';
import Button from '../components/Button';
import Card from '../components/Card';
import TextField from '../components/TextField';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'ProfileSetup'>;

/**
 * Feature 004, page 05: last onboarding step (after phone/OTP/PAN-KYC). Extracted out of the
 * old combined `Verification` screen so each onboarding step is its own real page/route.
 */
export default function ProfileSetupScreen({ route, navigation }: Props): React.JSX.Element {
  const { riderId, mode, initialName, initialGender } = route.params;
  const isEdit = mode === 'edit';
  const [displayName, setDisplayName] = useState(initialName ?? '');
  const [gender, setGender] =
    useState<'male' | 'female' | 'other' | 'undisclosed'>(initialGender ?? 'undisclosed');
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (): Promise<void> => {
    if (!displayName.trim()) {
      Alert.alert('Name required', 'Enter a display name to finish signing up.');
      return;
    }
    setSubmitting(true);
    try {
      await submitProfile(riderId, {
        display_name: displayName.trim(),
        gender,
        photo_url: '', // ponytail: no photo picker built yet — placeholder is fine (MVP)
      });
      if (isEdit) {
        navigation.goBack();
      } else {
        setAuthToken(riderId);
        navigation.reset({ index: 0, routes: [{ name: 'Home' }] });
      }
    } catch {
      Alert.alert('Error', 'Could not complete signup. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const genders: Array<'female' | 'male' | 'undisclosed'> = ['female', 'male', 'undisclosed'];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {!isEdit && (
        <View style={styles.stepper}>
          <View style={[styles.step, styles.stepDone]} />
          <View style={[styles.step, styles.stepDone]} />
          <View style={[styles.step, styles.stepDone]} />
          <View style={styles.step} />
        </View>
      )}
      <Card>
        <Text style={typography.heading}>{isEdit ? 'Edit profile' : 'Almost there'}</Text>
        <Text style={[typography.caption, styles.subtitle]}>
          Co-riders will see this — never your phone number
        </Text>
        <TextField
          label="Display name"
          value={displayName}
          onChangeText={setDisplayName}
          placeholder="Your name"
          autoFocus
        />
        <View style={styles.chipRow}>
          {genders.map((g) => (
            <Button
              key={g}
              title={g}
              variant={gender === g ? 'primary' : 'secondary'}
              onPress={() => setGender(g)}
              style={styles.chip}
            />
          ))}
        </View>
        <Button title={isEdit ? 'Save changes' : 'Finish signup'} onPress={onSubmit} loading={submitting} />
      </Card>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.md, justifyContent: 'center' },
  stepper: { flexDirection: 'row', gap: spacing.xs, marginBottom: spacing.lg },
  step: { flex: 1, height: 4, borderRadius: 2, backgroundColor: colors.border },
  stepDone: { backgroundColor: colors.primary },
  subtitle: { marginTop: spacing.xs, marginBottom: spacing.md },
  chipRow: { flexDirection: 'row', gap: spacing.xs, marginBottom: spacing.md },
  chip: { minHeight: 36, paddingVertical: spacing.xs, paddingHorizontal: spacing.sm + 4, minWidth: 0, borderRadius: 999 },
});
