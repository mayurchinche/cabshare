import React from 'react';
import { StyleSheet, type StyleProp, type ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { colors, gradients, radii, shadows, spacing } from '../theme';

type Props = {
  children: React.ReactNode;
  variant?: 'primary' | 'gold';
  style?: StyleProp<ViewStyle>;
};

/** The mockup's `.hero-gradient`/`.notice-banner` treatment — a full-bleed gradient card used for
 * the Home hero and (later) the live-train auto-booking banner. Kept as its own component
 * instead of another `Card` variant since the padding/radius numbers differ from a normal card. */
export default function GradientCard({ children, variant = 'primary', style }: Props): React.JSX.Element {
  const glow = shadows.glow(variant === 'primary' ? colors.primary : colors.accent);
  return (
    <LinearGradient
      colors={variant === 'primary' ? gradients.primary : gradients.gold}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.base, glow, style]}
    >
      {children}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radii.lg,
    padding: spacing.md + 6,
    marginBottom: spacing.md,
  },
});
