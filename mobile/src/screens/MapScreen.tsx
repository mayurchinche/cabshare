import React, { useCallback, useMemo, useRef, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { PROVIDER_GOOGLE, type LatLng, type Region } from 'react-native-maps';
import BottomSheet from '@gorhom/bottom-sheet';
import Animated, { useAnimatedStyle, useSharedValue } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import AnimatedDriverMarker from '../components/AnimatedDriverMarker';
import RideSelectionSheet, { type RideTier } from '../components/RideSelectionSheet';
import { colors, darkMapStyle, radii, shadows, spacing, typography } from '../theme';

/** Nearby driver as returned by the PostGIS proximity query. */
export type NearbyDriver = {
  id: string;
  coordinate: LatLng;
  heading?: number;
  stale?: boolean;
};

export type MapScreenProps = {
  initialRegion: Region;
  drivers: NearbyDriver[];
  tiers: RideTier[];
  onConfirm: (tierId: string) => void;
  /** Poll/push cadence of the driver-location feed, in ms. Must match the backend scheduler. */
  driverUpdateIntervalMs?: number;
};

/**
 * The main booking surface: full-bleed styled map with the ride-selection sheet docked over it.
 *
 * Layout rationale: the map is NOT inset for the sheet. It runs edge to edge behind it and we
 * instead push the *camera focus* upward via `mapPadding`, so the map's visual center lands in
 * the visible strip above the sheet. Insetting the map instead leaves a dead letterbox band and
 * makes the sheet look pasted on rather than floating.
 */
export default function MapScreen({
  initialRegion,
  drivers,
  tiers,
  onConfirm,
  driverUpdateIntervalMs,
}: MapScreenProps): React.JSX.Element {
  const insets = useSafeAreaInsets();
  const mapRef = useRef<MapView>(null);
  const sheetRef = useRef<BottomSheet>(null);

  const [selectedTierId, setSelectedTierId] = useState<string | null>(tiers[0]?.id ?? null);

  // Sheet's top edge in screen px, written by the sheet on the UI thread every frame. Floating
  // controls read this so they ride the sheet perfectly instead of lagging a frame behind.
  const sheetPosition = useSharedValue(0);

  // mapPadding is a *static* prop here, updated only on snap-point change rather than per frame.
  // Animating it every frame would push a native map-camera update 60x/sec, which visibly chokes
  // the Google Maps SDK on mid-range Android — a rare case where the non-animated path is the
  // correct engineering call.
  const [sheetIndex, setSheetIndex] = useState(0);
  const mapPadding = useMemo(
    () => ({
      top: insets.top + spacing.xl,
      right: 0,
      bottom: sheetIndex === 0 ? 260 : 520,
      left: 0,
    }),
    [insets.top, sheetIndex]
  );

  const recenterStyle = useAnimatedStyle(() => ({
    // 64px clear of the sheet's leading edge, tracked on the UI thread.
    transform: [{ translateY: sheetPosition.value - 64 }],
  }));

  const handleRecenter = useCallback(() => {
    mapRef.current?.animateCamera({ center: initialRegion, zoom: 15 }, { duration: 600 });
  }, [initialRegion]);

  const handleConfirm = useCallback(
    (tierId: string) => {
      sheetRef.current?.collapse();
      onConfirm(tierId);
    },
    [onConfirm]
  );

  return (
    <View style={styles.root}>
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFill}
        // Pinned to Google on BOTH platforms: `customMapStyle` is ignored by Apple Maps, so
        // defaulting to Apple on iOS would silently ship an unstyled bright map there.
        // Requires a Google Maps API key in app.json for ios.config.googleMapsApiKey.
        provider={PROVIDER_GOOGLE}
        customMapStyle={darkMapStyle}
        initialRegion={initialRegion}
        mapPadding={mapPadding}
        // Every default control is off: they're Google-branded, light-themed, and land in the
        // middle of our own UI. We re-provide only what's needed (recenter) in our own styling.
        showsCompass={false}
        showsMyLocationButton={false}
        showsPointsOfInterest={false}
        showsBuildings={false}
        showsTraffic={false}
        showsIndoors={false}
        toolbarEnabled={false}
        rotateEnabled={false}
        pitchEnabled={false}
        showsUserLocation
      >
        {drivers.map((driver) => (
          <AnimatedDriverMarker
            key={driver.id}
            coordinate={driver.coordinate}
            heading={driver.heading}
            stale={driver.stale}
            updateIntervalMs={driverUpdateIntervalMs}
          />
        ))}
      </MapView>

      <Animated.View style={[styles.recenter, recenterStyle]} pointerEvents="box-none">
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Recenter map on your location"
          onPress={handleRecenter}
          style={({ pressed }) => [styles.recenterButton, pressed && styles.recenterPressed]}
        >
          <Text style={styles.recenterGlyph}>◎</Text>
        </Pressable>
      </Animated.View>

      <RideSelectionSheet
        ref={sheetRef}
        tiers={tiers}
        selectedTierId={selectedTierId}
        onSelectTier={setSelectedTierId}
        onConfirm={handleConfirm}
        onIndexChange={setSheetIndex}
        animatedPosition={sheetPosition}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.background,
  },
  recenter: {
    position: 'absolute',
    right: spacing.lg,
    top: 0,
  },
  recenterButton: {
    width: 44,
    height: 44,
    borderRadius: radii.sm,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceSolid,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.card,
  },
  recenterPressed: { opacity: 0.8 },
  recenterGlyph: {
    ...typography.subheading,
    color: colors.accent,
    // Android centers glyphs slightly high in a fixed-height box; nudge it back onto the axis.
    lineHeight: Platform.OS === 'android' ? 22 : 20,
  },
});
