import React from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import { colors, gradients, radii, spacing, typography } from '../theme';

type ButtonVariant = 'primary' | 'gold' | 'secondary' | 'destructive';

type Props = {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  loading?: boolean;
  style?: StyleProp<ViewStyle>;
};

const VARIANT_TEXT: Record<ButtonVariant, string> = {
  primary: '#05060A',
  gold: '#201200',
  secondary: colors.textPrimary,
  destructive: colors.error,
};

/** Shared button with distinct default/pressed/disabled/loading visual states (FR-009).
 * `primary`/`gold` render the mockup's gradient fills via `expo-linear-gradient`; `secondary`/
 * `destructive` are flat per `design-system.css`'s `.btn-secondary`/`.btn-danger`. */
export default function Button({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  style,
}: Props): React.JSX.Element {
  const isDisabled = disabled || loading;
  const textColor = VARIANT_TEXT[variant];
  const content = loading ? (
    <ActivityIndicator color={textColor} />
  ) : (
    <Text style={[styles.text, { color: textColor }]}>{title}</Text>
  );

  if (variant === 'primary' || variant === 'gold') {
    return (
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ disabled: isDisabled, busy: loading }}
        onPress={isDisabled ? undefined : onPress}
        style={[isDisabled && styles.disabled, style]}
      >
        {({ pressed }) => (
          <LinearGradient
            colors={variant === 'primary' ? gradients.primary : gradients.gold}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[styles.base, pressed && !isDisabled && styles.pressed]}
          >
            {content}
          </LinearGradient>
        )}
      </Pressable>
    );
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      onPress={isDisabled ? undefined : onPress}
      style={({ pressed }) => [
        styles.base,
        variant === 'secondary' && styles.secondaryBg,
        variant === 'destructive' && styles.destructiveBg,
        pressed && !isDisabled && styles.pressed,
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingVertical: spacing.sm + 4,
    paddingHorizontal: spacing.md,
    borderRadius: radii.sm,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  secondaryBg: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.border,
  },
  destructiveBg: {
    backgroundColor: 'rgba(248,113,113,0.14)',
    borderWidth: 1,
    borderColor: 'rgba(248,113,113,0.3)',
  },
  pressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    ...typography.subheading,
    color: '#FFFFFF',
  },
});
