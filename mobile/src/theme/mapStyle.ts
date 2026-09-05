import { map } from './tokens';

/**
 * Google Maps style JSON for the premium dark map surface (consumed by `<MapView customMapStyle>`).
 *
 * Design intent: the map is *background*, not content. A stock Google map is a riot of competing
 * colors — green parks, yellow highways, blue water, red POI pins, transit lines — and dropping a
 * dark UI on top of it is the single biggest reason ride-hailing clones look cheap. So this style
 * does three things:
 *   1. Desaturates everything to a near-black land / true-black water base.
 *   2. Deletes all POI, transit, and business labels entirely (`visibility: off`) so the only
 *      labels left are the road/locality names a rider actually needs to orient themselves.
 *   3. Keeps a subtle 3-step road hierarchy (local < arterial < highway) in graded grays, so the
 *      street grid still reads as depth rather than mush.
 *
 * Result: the accent-champagne route line and driver marker are the ONLY saturated things on
 * screen, which is exactly where the rider's eye should go.
 *
 * PLATFORM NOTE: `customMapStyle` is applied by react-native-maps on Android (Google provider) and
 * on iOS only when `provider={PROVIDER_GOOGLE}`. With Apple Maps on iOS this prop is a no-op —
 * see MapScreen, which pins PROVIDER_GOOGLE on both platforms so the styling is identical.
 */
export const darkMapStyle = [
  // --- Base geometry -------------------------------------------------------
  { elementType: 'geometry', stylers: [{ color: map.land }] },
  { elementType: 'labels.icon', stylers: [{ visibility: 'off' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: map.label }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: map.labelStroke }] },

  // --- Kill the clutter ----------------------------------------------------
  // Every POI category off. Riders never need "nearby cafes" on a booking map, and POI pins are
  // what make a styled map still look unstyled.
  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
  { featureType: 'poi.business', stylers: [{ visibility: 'off' }] },
  { featureType: 'transit', stylers: [{ visibility: 'off' }] },
  // Parks keep geometry (so the city still has *shape*) but lose their labels and green tint.
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#0E1116' }] },
  { featureType: 'landscape.man_made', elementType: 'geometry', stylers: [{ color: '#0D0F15' }] },

  // --- Road hierarchy ------------------------------------------------------
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: map.roadLocal }] },
  { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: map.roadStroke }] },
  { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: map.label }] },
  { featureType: 'road.arterial', elementType: 'geometry', stylers: [{ color: map.roadArterial }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: map.roadHighway }] },
  { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: map.roadStroke }] },
  // Highway shields are loud and add nothing at booking zoom levels.
  { featureType: 'road.highway', elementType: 'labels.icon', stylers: [{ visibility: 'off' }] },
  { featureType: 'road.local', elementType: 'labels', stylers: [{ visibility: 'simplified' }] },

  // --- Water & admin -------------------------------------------------------
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: map.water }] },
  { featureType: 'water', elementType: 'labels.text', stylers: [{ visibility: 'off' }] },
  { featureType: 'administrative', elementType: 'geometry', stylers: [{ visibility: 'off' }] },
  {
    featureType: 'administrative.locality',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#7A8290' }],
  },
  {
    featureType: 'administrative.neighborhood',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#5C6273' }],
  },
];

export default darkMapStyle;
