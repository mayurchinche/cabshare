import React, { forwardRef, useCallback, useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import BottomSheet, {
  BottomSheetBackdrop,
  BottomSheetView,
  useBottomSheetSpringConfigs,
  type BottomSheetBackdropProps,
  type BottomSheetBackgroundProps,
} from '@gorhom/bottom-sheet';
import { BlurView } from 'expo-blur';
import Animated, {
  interpolate,
  useAnimatedStyle,
  useDerivedValue,
  useSharedValue,
  withSpring,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';

import { colors, motion, radii, spacing, typography } from '../theme';

export type RideTier = {
  id: string;
  name: string;
  /** Short value prop, e.g. "Shared sedan · up to 2 co-riders". */
  description: string;
  /** Already-formatted for display — formatting money in the component invites locale bugs. */
  fare: string;
  etaMinutes: number;
  seats: number;
};

export type RideSelectionSheetProps = {
  tiers: RideTier[];
  selectedTierId: string | null;
  onSelectTier: (tierId: string) => void;
  onConfirm: (tierId: string) => void;
  /** Sheet position index changes bubble up so the map can re-pad its bottom inset. */
  onIndexChange?: (index: number) => void;
  /** Driven by the parent so the map's `mapPadding` can track the sheet in real time. */
  animatedPosition?: SharedValue<number>;
};

/**
 * The primary booking surface: a spring-driven bottom sheet for picking a ride tier.
 *
 * Motion design rationale:
 *   - Springs, not durations. A `withTiming` sheet always feels mechanical because real objects
 *     don't move at a fixed rate; the spring in `motion.sheetSpring` is tuned near-critically-
 *     damped so it settles fast with only a hint of overshoot. Bouncy springs read as playful,
 *     which is the opposite of the brief.
 *   - Content responds to sheet position. The header collapses and the tier rows stagger in as
 *     the sheet expands, driven off `animatedIndex` — a sheet whose contents are static while
 *     the container moves feels like a photo on a slider.
 */
const RideSelectionSheet = forwardRef<BottomSheet, RideSelectionSheetProps>(
  function RideSelectionSheet(
    { tiers, selectedTierId, onSelectTier, onConfirm, onIndexChange, animatedPosition },
    ref
  ) {
    // Collapsed = peek at the cheapest tier; expanded = full comparison. Percentages (not px)
    // so the sheet holds its proportions from an SE to a Pro Max.
    const snapPoints = useMemo(() => ['32%', '72%'], []);

    const animatedIndex = useSharedValue(0);

    const springConfig = useBottomSheetSpringConfigs(motion.sheetSpring);

    const renderBackdrop = useCallback(
      (props: BottomSheetBackdropProps) => (
        <BottomSheetBackdrop
          {...props}
          appearsOnIndex={1}
          disappearsOnIndex={0}
          opacity={0.6}
          pressBehavior="collapse"
        />
      ),
      []
    );

    // Header shrinks as the sheet opens: at collapsed it's a big "Choose your ride" title, at
    // expanded it tightens to give the list room. Pure UI-thread interpolation.
    const headerStyle = useAnimatedStyle(() => ({
      opacity: interpolate(animatedIndex.value, [0, 1], [1, 0.85]),
      transform: [{ translateY: interpolate(animatedIndex.value, [0, 1], [0, -4]) }],
    }));

    const hintStyle = useAnimatedStyle(() => ({
      // The "drag for more options" affordance is only true while collapsed, so it fades out
      // exactly as it stops being true.
      opacity: interpolate(animatedIndex.value, [0, 0.5], [1, 0], 'clamp'),
      height: interpolate(animatedIndex.value, [0, 0.5], [18, 0], 'clamp'),
    }));

    const handleChange = useCallback(
      (index: number) => {
        animatedIndex.value = index;
        onIndexChange?.(index);
      },
      [animatedIndex, onIndexChange]
    );

    const selectedTier = tiers.find((t) => t.id === selectedTierId) ?? null;

    return (
      <BottomSheet
        ref={ref}
        index={0}
        snapPoints={snapPoints}
        animationConfigs={springConfig}
        animatedPosition={animatedPosition}
        animatedIndex={animatedIndex}
        onChange={handleChange}
        enablePanDownToClose={false}
        backdropComponent={renderBackdrop}
        handleIndicatorStyle={styles.handleIndicator}
        backgroundComponent={SheetBackground}
      >
        <BottomSheetView style={styles.content}>
          <Animated.View style={headerStyle}>
            <Text style={styles.overline}>Choose your ride</Text>
            <Animated.View style={hintStyle}>
              <Text style={styles.hint}>Drag up to compare all options</Text>
            </Animated.View>
          </Animated.View>

          <View style={styles.list}>
            {tiers.map((tier, index) => (
              <TierRow
                key={tier.id}
                tier={tier}
                index={index}
                selected={tier.id === selectedTierId}
                onPress={() => onSelectTier(tier.id)}
                animatedIndex={animatedIndex}
              />
            ))}
          </View>

          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: !selectedTier }}
            disabled={!selectedTier}
            onPress={() => selectedTier && onConfirm(selectedTier.id)}
            style={({ pressed }) => [
              styles.cta,
              !selectedTier && styles.ctaDisabled,
              pressed && styles.ctaPressed,
            ]}
          >
            <Text style={styles.ctaLabel}>
              {selectedTier ? `Confirm ${selectedTier.name}` : 'Select a ride'}
            </Text>
          </Pressable>
        </BottomSheetView>
      </BottomSheet>
    );
  }
);

/** Frosted sheet background. A translucent blur over the dark map (rather than an opaque panel)
 * is what gives the sheet the sense of floating above the world instead of covering it. */
function SheetBackground({ style }: BottomSheetBackgroundProps): React.JSX.Element {
  return (
    <View style={[style, styles.sheetBackground]}>
      <BlurView intensity={60} tint="dark" style={StyleSheet.absoluteFill} />
    </View>
  );
}

type TierRowProps = {
  tier: RideTier;
  index: number;
  selected: boolean;
  onPress: () => void;
  animatedIndex: SharedValue<number>;
};

function TierRow({ tier, index, selected, onPress, animatedIndex }: TierRowProps): React.JSX.Element {
  const pressed = useSharedValue(0);

  // Staggered reveal: each row past the first is offset slightly further, so rows appear to
  // cascade in as the sheet opens rather than all snapping at once. `useDerivedValue` keeps the
  // whole computation on the UI thread.
  const stagger = useDerivedValue(() => {
    const start = Math.min(index * 0.12, 0.5);
    return interpolate(animatedIndex.value, [start, start + 0.5], [0, 1], 'clamp');
  });

  const rowStyle = useAnimatedStyle(() => {
    // Row 0 is visible while collapsed (it's the peek row); later rows fade in on expand.
    const reveal = index === 0 ? 1 : stagger.value;
    return {
      opacity: reveal,
      transform: [
        { translateY: (1 - reveal) * 12 },
        { scale: withSpring(pressed.value ? 0.98 : 1, motion.controlSpring) },
      ],
    };
  });

  const selectionStyle = useAnimatedStyle(() => ({
    borderColor: withTiming(selected ? colors.accent : colors.border, {
      duration: motion.fadeMs,
    }),
    backgroundColor: withTiming(
      selected ? 'rgba(200,169,122,0.10)' : 'rgba(255,255,255,0.03)',
      { duration: motion.fadeMs }
    ),
  }));

  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ selected }}
      accessibilityLabel={`${tier.name}, ${tier.fare}, ${tier.etaMinutes} minutes away`}
      onPress={onPress}
      onPressIn={() => {
        pressed.value = 1;
      }}
      onPressOut={() => {
        pressed.value = 0;
      }}
    >
      <Animated.View style={[styles.row, rowStyle, selectionStyle]}>
        <View style={styles.rowMain}>
          <Text style={styles.tierName}>{tier.name}</Text>
          <Text style={styles.tierDescription} numberOfLines={1}>
            {tier.description}
          </Text>
        </View>
        <View style={styles.rowMeta}>
          <Text style={styles.fare}>{tier.fare}</Text>
          <Text style={styles.eta}>{tier.etaMinutes} min</Text>
        </View>
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  sheetBackground: {
    backgroundColor: 'rgba(10,12,17,0.72)',
    borderTopLeftRadius: radii.lg,
    borderTopRightRadius: radii.lg,
    borderTopWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  handleIndicator: {
    backgroundColor: colors.textTertiary,
    width: 36,
    height: 4,
  },
  content: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
  },
  overline: {
    ...typography.overline,
    marginBottom: spacing.xs,
  },
  hint: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  list: {
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: radii.md,
    borderWidth: 1,
  },
  rowMain: { flex: 1, paddingRight: spacing.sm },
  rowMeta: { alignItems: 'flex-end' },
  tierName: { ...typography.subheading },
  tierDescription: { ...typography.caption, marginTop: 2 },
  fare: { ...typography.subheading },
  eta: { ...typography.caption, color: colors.textTertiary, marginTop: 2 },
  cta: {
    marginTop: spacing.lg,
    height: 54,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.accent,
  },
  ctaDisabled: { backgroundColor: colors.accentMuted, opacity: 0.5 },
  ctaPressed: { opacity: 0.85 },
  ctaLabel: {
    ...typography.subheading,
    color: colors.background,
  },
});

export default RideSelectionSheet;
