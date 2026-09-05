import React, { useEffect, useMemo, useRef } from 'react';
import { StyleSheet, View } from 'react-native';
import { AnimatedRegion, MarkerAnimated, type LatLng } from 'react-native-maps';
import Animated, {
  Easing,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';

import { colors, map, motion } from '../theme';

export type DriverMarkerProps = {
  /** Latest coordinate pushed from the backend (APScheduler -> PostGIS -> websocket/poll). */
  coordinate: LatLng;
  /**
   * Expected ms between backend pushes. The position tween is stretched to exactly this long so
   * the car is *always* still moving when the next fix lands — that continuous motion is what
   * sells "live tracking". Too short and you get move-freeze-move stutter.
   */
  updateIntervalMs?: number;
  /** Heading in degrees (0 = north). If omitted it's derived from consecutive coordinates. */
  heading?: number;
  /** Dims the marker + stops the halo when the driver hasn't reported in recently. */
  stale?: boolean;
  children?: React.ReactNode;
};

const EARTH_RADIUS_GUARD = 1e-9;

/** Great-circle initial bearing, in degrees clockwise from north. Runs on the JS thread (once per
 * backend fix, not per frame) so plain Math is fine here. */
function bearingBetween(from: LatLng, to: LatLng): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLon = toRad(to.longitude - from.longitude);
  const lat1 = toRad(from.latitude);
  const lat2 = toRad(to.latitude);
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  if (Math.abs(x) < EARTH_RADIUS_GUARD && Math.abs(y) < EARTH_RADIUS_GUARD) return 0;
  return (((Math.atan2(y, x) * 180) / Math.PI) + 360) % 360;
}

/**
 * Live driver marker that glides between GPS fixes instead of teleporting.
 *
 * ARCHITECTURE NOTE — why this is a hybrid and not pure Reanimated:
 * `<Marker coordinate>` is a native prop on a native view that Reanimated has no bindings for.
 * Driving it from a Reanimated shared value would mean `useAnimatedReaction` + `runOnJS` +
 * `setState` at 60fps, i.e. a full React re-render every frame — the exact jank we're removing.
 * react-native-maps ships the supported path for this: `AnimatedRegion` + `MarkerAnimated`, which
 * hands the tween to the platform map SDK.
 *
 * So responsibilities split cleanly:
 *   - POSITION  -> AnimatedRegion (native map SDK interpolation).
 *   - ROTATION + HALO + SCALE -> Reanimated worklets on the UI thread (these are ordinary RN
 *     views inside the marker, which Reanimated *can* drive without touching JS).
 *
 * Both are off the JS thread, which is the property that actually matters.
 */
export default function AnimatedDriverMarker({
  coordinate,
  updateIntervalMs = motion.markerDurationMs,
  heading,
  stale = false,
  children,
}: DriverMarkerProps): React.JSX.Element {
  const reduceMotion = useReducedMotion();

  // AnimatedRegion is imperative + must survive re-renders, so it lives in a ref and is seeded
  // once with the first coordinate (seeding it in state would re-create the tween every render).
  const regionRef = useRef(
    new AnimatedRegion({
      latitude: coordinate.latitude,
      longitude: coordinate.longitude,
      latitudeDelta: 0,
      longitudeDelta: 0,
    })
  );
  const previousCoordinate = useRef<LatLng>(coordinate);

  // Continuous (non-wrapping) bearing. Storing the *unwrapped* angle is what stops the car from
  // spinning 350deg counter-clockwise when it crosses north (359 -> 1).
  const rotation = useSharedValue(heading ?? 0);
  const pulse = useSharedValue(0);

  useEffect(() => {
    const from = previousCoordinate.current;
    const moved =
      from.latitude !== coordinate.latitude || from.longitude !== coordinate.longitude;

    if (moved) {
      const next = heading ?? bearingBetween(from, coordinate);
      // Shortest-path unwrap: fold the delta into [-180, 180] and add it to the running angle.
      const delta = (((next - (rotation.value % 360)) % 360) + 540) % 360 - 180;
      rotation.value = reduceMotion
        ? rotation.value + delta
        : withTiming(rotation.value + delta, {
            duration: updateIntervalMs * 0.6,
            easing: Easing.out(Easing.quad),
          });
    }

    if (reduceMotion) {
      // Respect the OS "reduce motion" setting: jump straight to the fix, no tween.
      regionRef.current.setValue({
        latitude: coordinate.latitude,
        longitude: coordinate.longitude,
        latitudeDelta: 0,
        longitudeDelta: 0,
      });
    } else {
      const animation = regionRef.current.timing({
        latitude: coordinate.latitude,
        longitude: coordinate.longitude,
        latitudeDelta: 0,
        longitudeDelta: 0,
        duration: updateIntervalMs,
        // MUST stay false: AnimatedRegion drives a native map prop, not a transform, so the
        // native driver has nothing to attach to and will throw if enabled.
        useNativeDriver: false,
        toValue: 0,
      });
      animation.start();
      previousCoordinate.current = coordinate;
      return () => animation.stop();
    }

    previousCoordinate.current = coordinate;
    return undefined;
  }, [coordinate, heading, updateIntervalMs, reduceMotion, rotation]);

  // Slow "breathing" halo — the ambient signal that the position is live rather than a last-known
  // dot. Suppressed when stale so a frozen driver doesn't look active.
  useEffect(() => {
    if (reduceMotion || stale) {
      pulse.value = withTiming(0, { duration: motion.fadeMs });
      return;
    }
    pulse.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1600, easing: Easing.out(Easing.quad) }),
        withTiming(0, { duration: 0 })
      ),
      -1,
      false
    );
  }, [reduceMotion, stale, pulse]);

  const haloStyle = useAnimatedStyle(() => ({
    transform: [{ scale: 1 + pulse.value * 1.6 }],
    opacity: (1 - pulse.value) * 0.9,
  }));

  const bodyStyle = useAnimatedStyle(() => ({
    transform: [{ rotateZ: `${rotation.value}deg` }],
  }));

  const staleStyle = useAnimatedStyle(() => ({
    opacity: withTiming(stale ? 0.45 : 1, { duration: motion.fadeMs }),
  }));

  // `anchor` centers the marker on its coordinate; without it the map anchors at the bottom edge
  // and the car visibly sits north of where the driver actually is.
  const anchor = useMemo(() => ({ x: 0.5, y: 0.5 }), []);

  return (
    <MarkerAnimated
      coordinate={regionRef.current as unknown as LatLng}
      anchor={anchor}
      flat
      tracksViewChanges={false}
      accessibilityLabel="Driver location"
    >
      <Animated.View style={[styles.container, staleStyle]}>
        <Animated.View style={[styles.halo, haloStyle]} pointerEvents="none" />
        <Animated.View style={[styles.body, bodyStyle]}>
          {children ?? (
            <View style={styles.chevron}>
              <View style={styles.chevronCore} />
            </View>
          )}
        </Animated.View>
      </Animated.View>
    </MarkerAnimated>
  );
}

const MARKER = 44;

const styles = StyleSheet.create({
  container: {
    width: MARKER,
    height: MARKER,
    alignItems: 'center',
    justifyContent: 'center',
  },
  halo: {
    position: 'absolute',
    width: MARKER * 0.6,
    height: MARKER * 0.6,
    borderRadius: MARKER * 0.3,
    backgroundColor: map.driverHalo,
  },
  body: {
    width: MARKER * 0.55,
    height: MARKER * 0.55,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Default puck: a directional chevron, not a literal car sprite. A flat geometric puck reads
  // more premium at small sizes than a skeuomorphic vehicle icon, and it scales cleanly.
  chevron: {
    width: 0,
    height: 0,
    borderLeftWidth: 8,
    borderRightWidth: 8,
    borderBottomWidth: 18,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderBottomColor: colors.accent,
    alignItems: 'center',
  },
  chevronCore: {
    position: 'absolute',
    top: 8,
    left: -3,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.background,
  },
});
