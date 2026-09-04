import React, { useEffect } from 'react';
import { Image, StyleSheet, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../navigation/AppNavigator';
import { getAuthToken } from '../services/apiClient';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Splash'>;

/**
 * Feature 004, page 01: brand load + auth-token check. `getAuthToken()` is the in-memory-only
 * MVP auth stand-in (see `apiClient.ts`) — there is no persisted session yet, so this always
 * routes to `Verification` today; the check is left in place so wiring a real persisted token
 * later is a one-line change here, not a new screen.
 */
export default function SplashScreen({ navigation }: Props): React.JSX.Element {
  useEffect(() => {
    const timer = setTimeout(() => {
      const riderId = getAuthToken();
      navigation.reset({
        index: 0,
        routes: [{ name: riderId ? 'Home' : 'Verification' }],
      });
    }, 900);
    return () => clearTimeout(timer);
  }, [navigation]);

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <Image
        source={require('../../assets/splash-icon.png')}
        style={styles.logo}
        resizeMode="contain"
      />
      <Text style={styles.subtitle}>Share the ride. Split the fare.</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  logo: {
    width: 280,
    height: 280,
    marginBottom: spacing.sm,
  },
  title: { ...typography.heading },
  subtitle: { ...typography.caption },
});
