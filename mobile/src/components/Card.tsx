import React from 'react';
import { Pressable, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import { BlurView } from 'expo-blur';

import { colors, radii, shadows, spacing } from '../theme';

type Props = {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
};

/** Shared elevated container used for grouping content on every screen (FR-009). Real
 * glassmorphism (BlurView + translucent tint + soft shadow) instead of a flat opaque box —
 * this is the single biggest lever for the "premium unicorn app" look since every screen
 * composes its content from this one component. Renders as a `Pressable` when `onPress` is
 * given (e.g. a tappable ride-history row), a plain `View` otherwise. */
export default function Card({ children, style, onPress }: Props): React.JSX.Element {
  const body = (
    <View style={[styles.card, style]}>
      <BlurView intensity={40} tint="dark" style={StyleSheet.absoluteFill} />
      <View style={styles.content}>{children}</View>
    </View>
  );

  if (onPress) {
    return (
      <Pressable onPress={onPress} style={({ pressed }) => pressed && styles.pressed}>
        {body}
      </Pressable>
    );
  }
  return body;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    marginBottom: spacing.sm + 2,
    overflow: 'hidden',
    ...shadows.card,
  },
  content: {
    padding: spacing.md,
  },
  pressed: {
    opacity: 0.85,
    transform: [{ scale: 0.985 }],
  },
});
