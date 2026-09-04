import React, { useRef } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { colors, radii, spacing, typography } from '../theme';

type Props = {
  length?: number;
  value: string;
  onChangeText: (value: string) => void;
  autoFocus?: boolean;
};

/**
 * Hand-built segmented OTP box input (no third-party dependency, per plan.md's zero-new-deps
 * decision). Renders `length` boxes but is backed by a SINGLE real `TextInput` positioned over
 * them — this is deliberate: a single native input is what reliably brings up the on-screen
 * keyboard/number pad on Android emulators (the multi-input-per-box approach is what caused the
 * "no keypad appears" bug seen earlier in this project). Tapping any box focuses the real input.
 */
export default function SegmentedCodeInput({
  length = 6,
  value,
  onChangeText,
  autoFocus = true,
}: Props): React.JSX.Element {
  const inputRef = useRef<TextInput>(null);
  const digits = value.split('').slice(0, length);

  return (
    <Pressable onPress={() => inputRef.current?.focus()} style={styles.wrapper}>
      <View style={styles.boxRow} pointerEvents="none">
        {Array.from({ length }).map((_, i) => {
          const filled = digits[i] !== undefined;
          const isActive = i === digits.length;
          return (
            <View
              key={i}
              style={[styles.box, isActive && styles.boxActive, filled && styles.boxFilled]}
            >
              <Text style={styles.digit}>{digits[i] ?? ''}</Text>
            </View>
          );
        })}
      </View>
      <TextInput
        ref={inputRef}
        value={value}
        onChangeText={(text) => onChangeText(text.replace(/[^0-9]/g, '').slice(0, length))}
        keyboardType="number-pad"
        autoFocus={autoFocus}
        maxLength={length}
        style={styles.hiddenInput}
        accessibilityLabel="One-time passcode"
        importantForAutofill="yes"
        textContentType="oneTimeCode"
      />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'relative',
  },
  boxRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  box: {
    width: 44,
    height: 52,
    borderRadius: radii.sm,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: 'rgba(255,255,255,0.03)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  boxActive: {
    borderColor: colors.borderFocused,
    borderWidth: 2,
  },
  boxFilled: {
    borderColor: colors.accentViolet,
  },
  digit: {
    ...typography.heading,
    fontSize: 20,
  },
  hiddenInput: {
    position: 'absolute',
    opacity: 0,
    width: '100%',
    height: 52,
    top: 0,
    left: 0,
  },
});
