import React, { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, StyleSheet, Text, View } from 'react-native';

import { colors, spacing, typography } from '../theme';

type CarMotionState = 'idle' | 'searching' | 'success';

type Props = {
  state?: CarMotionState;
  caption?: string;
};

/**
 * The app's signature ride-themed motif (FR-010): two "cars" (rider + co-rider) drive toward
 * each other and meet in the middle, used on verification/matching success states to make the
 * "you + a nearby co-rider" concept feel tangible instead of a generic spinner.
 *
 * Built with React Native's core `Animated` API only (no `react-native-reanimated`/Lottie,
 * per plan.md's zero-new-dependency decision). Honors the OS "reduce motion" setting by
 * skipping to a static end-state instead of looping (accessibility requirement).
 */
export default function CarMotion({ state = 'idle', caption }: Props): React.JSX.Element {
  const progress = useRef(new Animated.Value(0)).current;
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled?.()
      .then(setReduceMotion)
      .catch(() => setReduceMotion(false));
  }, []);

  useEffect(() => {
    if (reduceMotion) {
      progress.setValue(state === 'success' ? 1 : 0.5);
      return;
    }

    if (state === 'searching') {
      const loop = Animated.loop(
        Animated.sequence([
          Animated.timing(progress, {
            toValue: 1,
            duration: 1400,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(progress, {
            toValue: 0,
            duration: 0,
            useNativeDriver: true,
          }),
        ])
      );
      loop.start();
      return () => loop.stop();
    }

    Animated.timing(progress, {
      toValue: state === 'success' ? 1 : 0,
      duration: 500,
      easing: Easing.out(Easing.ease),
      useNativeDriver: true,
    }).start();
    return undefined;
  }, [state, reduceMotion, progress]);

  const leftCarTranslate = progress.interpolate({ inputRange: [0, 1], outputRange: [0, 90] });
  const rightCarTranslate = progress.interpolate({ inputRange: [0, 1], outputRange: [0, -90] });
  const meetScale = progress.interpolate({ inputRange: [0, 0.9, 1], outputRange: [1, 1, 1.15] });

  return (
    <View style={styles.container}>
      <View style={styles.track}>
        <Animated.View
          style={[styles.car, styles.carLeft, { transform: [{ translateX: leftCarTranslate }] }]}
        >
          <Text style={styles.carEmoji}>🚗</Text>
        </Animated.View>
        <Animated.View style={[styles.meetDot, { transform: [{ scale: meetScale }] }]} />
        <Animated.View
          style={[
            styles.car,
            styles.carRight,
            { transform: [{ translateX: rightCarTranslate }] },
          ]}
        >
          <Text style={styles.carEmoji}>🚕</Text>
        </Animated.View>
      </View>
      {caption ? <Text style={styles.caption}>{caption}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    paddingVertical: spacing.lg,
  },
  track: {
    width: 220,
    height: 60,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  car: {
    width: 40,
    alignItems: 'center',
  },
  carLeft: { alignItems: 'flex-start' },
  carRight: { alignItems: 'flex-end' },
  carEmoji: { fontSize: 32 },
  meetDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.accent,
  },
  caption: {
    ...typography.caption,
    marginTop: spacing.sm,
  },
});
