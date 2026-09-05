import React, { useEffect, useRef, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { confirmOtp, requestOtp, setAuthToken } from '../services/apiClient';
import type { RootStackParamList } from '../navigation/AppNavigator';
import Button from '../components/Button';
import Card from '../components/Card';
import CarMotion from '../components/CarMotion';
import SegmentedCodeInput from '../components/SegmentedCodeInput';
import TextField from '../components/TextField';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Verification'>;

type Step = 'phone' | 'otp';

const RESEND_COOLDOWN_SECONDS = 30;

/**
 * FR-011 signup/login: phone + OTP only. Feature 004 split what used to be a combined
 * phone→otp→profile screen into separate routes per the new onboarding order: phone/OTP here,
 * then PAN/KYC (`PanKyc`), then `ProfileSetup`, then `Home` — see `AppNavigator`'s nav map.
 */
export default function VerificationScreen({ navigation }: Props): React.JSX.Element {
  const [step, setStep] = useState<Step>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [debugOtpCode, setDebugOtpCode] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [otpError, setOtpError] = useState<string | undefined>(undefined);
  const [verified, setVerified] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const cooldownTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (cooldownTimer.current) clearInterval(cooldownTimer.current);
    };
  }, []);

  const startCooldown = (): void => {
    setCooldown(RESEND_COOLDOWN_SECONDS);
    if (cooldownTimer.current) clearInterval(cooldownTimer.current);
    cooldownTimer.current = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          if (cooldownTimer.current) clearInterval(cooldownTimer.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const onRequestOtp = async (): Promise<void> => {
    if (!phoneNumber) {
      Alert.alert('Phone number required', 'Enter your phone number to continue.');
      return;
    }
    setSubmitting(true);
    try {
      const result = await requestOtp(phoneNumber);
      setDebugOtpCode(result.debug_otp_code); // ponytail: dev-only, no real SMS provider yet
      setStep('otp');
      startCooldown();
    } catch {
      Alert.alert('Error', 'Could not request an OTP. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const onConfirmOtp = async (): Promise<void> => {
    if (otpCode.length < 6) {
      setOtpError('Enter the 6-digit code sent to your phone.');
      return;
    }
    setOtpError(undefined);
    setSubmitting(true);
    try {
      const result = await confirmOtp(phoneNumber, otpCode);
      setVerified(true);
      setTimeout(() => {
        if (result.needs_kyc) {
          navigation.navigate('PanKyc', { riderId: result.rider_id });
        } else if (result.needs_profile) {
          navigation.navigate('ProfileSetup', { riderId: result.rider_id });
        } else {
          setAuthToken(result.rider_id);
          navigation.reset({ index: 0, routes: [{ name: 'Home' }] });
        }
      }, 700);
    } catch {
      setOtpError('That code is wrong or has expired — please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const motionState = verified ? 'success' : submitting ? 'searching' : 'idle';

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <CarMotion
          state={motionState}
          caption={
            verified
              ? "You're verified — let's find your ride"
              : step === 'phone'
              ? 'Your co-riders are already on the way'
              : undefined
          }
        />

        {step === 'phone' && (
          <Card>
            <Text style={typography.heading}>Welcome to CabShare</Text>
            <Text style={[typography.caption, styles.subtitle]}>
              Enter your phone number to get started
            </Text>
            <TextField
              label="Phone number"
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              placeholder="+91XXXXXXXXXX"
              keyboardType="phone-pad"
              autoFocus
            />
            <Button title="Send OTP" onPress={onRequestOtp} loading={submitting} />
          </Card>
        )}

        {step === 'otp' && (
          <Card>
            <Text style={typography.heading}>Verify your number</Text>
            <Text style={[typography.caption, styles.subtitle]}>
              Enter the 6-digit code sent to {phoneNumber}
            </Text>
            {/* ponytail: shown in release builds too until a paid SMS provider is wired in —
                friend-testers need to see the fixed code since no real text is sent. */}
            {debugOtpCode ? (
              <Text style={styles.devHint}>(no SMS sent yet — code: {debugOtpCode})</Text>
            ) : null}
            <View style={styles.otpWrapper}>
              <SegmentedCodeInput value={otpCode} onChangeText={setOtpCode} />
            </View>
            {otpError ? <Text style={styles.errorText}>{otpError}</Text> : null}
            <Button title="Confirm" onPress={onConfirmOtp} loading={submitting} />
            <Button
              title={cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend code'}
              variant="secondary"
              onPress={onRequestOtp}
              disabled={cooldown > 0}
              style={styles.resendButton}
            />
          </Card>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: {
    flexGrow: 1,
    padding: spacing.md,
    justifyContent: 'center',
  },
  subtitle: {
    marginTop: spacing.xs,
    marginBottom: spacing.md,
  },
  devHint: {
    ...typography.caption,
    color: colors.warning,
    marginBottom: spacing.sm,
  },
  otpWrapper: {
    marginBottom: spacing.sm,
  },
  errorText: {
    ...typography.caption,
    color: colors.error,
    marginBottom: spacing.sm,
  },
  resendButton: {
    marginTop: spacing.sm,
  },
});
