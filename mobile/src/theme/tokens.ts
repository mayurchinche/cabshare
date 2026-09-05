/**
 * Shared design tokens (Feature 004: CRED/INDMoney-tier premium dark theme). Values map 1:1 to
 * `specs/004-full-app-experience/mockups/design-system.css` (the signed-off visual reference) —
 * every screen/component MUST import from here instead of hardcoding colors/spacing/type, so
 * changing the palette never means hunting through every screen file.
 */
export const colors = {
  background: '#05060A',
  // ponytail: matches design-system.css's --surface exactly — a translucent white overlay
  // over the dark bg gives cards visible "lift"/depth (the CRED/INDMoney glass look). This was
  // previously flattened to an opaque solid, which made every card blend into the background
  // with zero contrast — the actual root cause of the "not premium" feedback.
  surface: 'rgba(255,255,255,0.045)',
  surfaceSolid: '#12141B', // opaque variant for nav backgrounds where translucency is wrong
  surfaceRaised: '#1A1D26',
  border: 'rgba(255,255,255,0.09)',
  // --- Single accent ramp (champagne) -------------------------------------
  // The premium refresh collapses the old three-accent system (violet + gold + teal) down to
  // ONE sophisticated accent. Three competing saturated hues on a near-black canvas is what
  // reads as "consumer app" rather than "luxury service"; a single low-chroma warm metallic
  // against pitch black is the standard luxury-transport signature.
  // Chroma is deliberately low (~28% sat) — bright primaries are the thing to avoid here.
  accentMuted: '#8A7454', // de-emphasised / disabled accent, borders
  accent: '#C8A97A', // canonical accent — CTAs, selected states, active marker
  accentBright: '#E3CBA1', // hover/pressed highlight, gradient top stop

  primary: '#C8A97A',
  primaryPressed: '#8A7454',
  secondary: '#12141B',

  // Deprecated aliases. Kept so the 17 existing screens that import `accentViolet`/`accentTeal`
  // keep compiling; they now resolve to the single accent so the app is visually consistent
  // during migration. Delete once every call site imports `accent` directly.
  /** @deprecated use `accent` */
  accentTeal: '#C8A97A',
  /** @deprecated use `accent` */
  accentViolet: '#C8A97A',
  /** @deprecated use `accent` */
  accentGold: '#C8A97A',

  textPrimary: '#F5F6FA',
  textSecondary: '#9AA1B2',
  textTertiary: '#5C6273',
  borderFocused: '#C8A97A',
  error: '#F87171',
  success: '#34D399',
  warning: '#FBBF24',
};

/** Gradient stop pairs for `expo-linear-gradient`. Now single-hue (champagne light -> dark)
 * instead of the old violet->teal rainbow: a tonal gradient inside one hue family is what keeps
 * the surface looking like brushed metal rather than a gaming app. */
export const gradients = {
  primary: ['#E3CBA1', '#C8A97A'] as const,
  gold: ['#E3CBA1', '#8A7454'] as const,
  /** Top-down scrim laid over the map so the sheet's top edge never fights the map tiles. */
  mapScrim: ['rgba(5,6,10,0)', 'rgba(5,6,10,0.85)'] as const,
};

/** Map-surface specific colors. Kept separate from the UI palette because these are consumed by
 * the Google Maps style JSON (which needs raw hex, no rgba) and by the marker/route overlays. */
export const map = {
  land: '#0B0D12',
  water: '#05060A',
  roadArterial: '#1C1F27',
  roadLocal: '#141720',
  roadHighway: '#252932',
  roadStroke: '#0B0D12',
  label: '#6B7280',
  labelStroke: '#05060A',
  route: '#C8A97A',
  routeCasing: 'rgba(200,169,122,0.25)',
  driverHalo: 'rgba(200,169,122,0.18)',
};

/** Shared motion constants. Centralised so every spring in the app has the same "weight" —
 * mismatched spring configs across components is the most common reason an app feels
 * assembled from parts instead of designed. Tuned critically-damped-ish (no visible wobble):
 * luxury UI overshoots very little. */
export const motion = {
  /** Sheet snap + large surface movement. */
  sheetSpring: { damping: 34, stiffness: 260, mass: 1 },
  /** Small control feedback (pressed states, selection ticks). */
  controlSpring: { damping: 22, stiffness: 340, mass: 0.7 },
  /** Driver marker position lerp. Must be >= the backend push interval or the car stutters. */
  markerDurationMs: 1000,
  /** Duration for opacity/scale cross-fades. */
  fadeMs: 220,
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

/** Modular type scale (1.185 minor-third-ish, rounded to whole px so text stays crisp on
 * Android's non-subpixel text rendering). Use these instead of inline fontSize literals so the
 * whole app can be rescaled from one place. */
export const fontSize = {
  micro: 11,
  caption: 13,
  body: 15,
  subheading: 17,
  title: 20,
  heading: 24,
  display: 34,
};

export const typography = {
  /** Large numeric/price display — the fare figure on the ride sheet. Tight tracking at large
   * sizes is what separates a premium type setting from a default one. */
  display: {
    fontSize: fontSize.display,
    fontWeight: '700' as const,
    color: colors.textPrimary,
    letterSpacing: -1,
  },
  heading: { fontSize: fontSize.heading, fontWeight: '700' as const, color: colors.textPrimary, letterSpacing: -0.3 },
  title: { fontSize: fontSize.title, fontWeight: '600' as const, color: colors.textPrimary, letterSpacing: -0.2 },
  subheading: { fontSize: fontSize.subheading, fontWeight: '600' as const, color: colors.textPrimary, letterSpacing: -0.1 },
  body: { fontSize: fontSize.body, fontWeight: '400' as const, color: colors.textPrimary },
  caption: { fontSize: fontSize.caption, fontWeight: '400' as const, color: colors.textSecondary },
  // Tracked-out uppercase micro-label — the "SECTION HEADER" / button-caption look every
  // unicorn fintech app (CRED, PhonePe, INDMoney) uses for section eyebrows and pill labels.
  overline: {
    fontSize: 11,
    fontWeight: '700' as const,
    color: colors.textSecondary,
    letterSpacing: 1.2,
    textTransform: 'uppercase' as const,
  },
};

export const radii = {
  sm: 12,
  md: 20,
  lg: 28,
};

// Soft, colored depth — flat opaque cards with zero shadow is what makes an app look like a
// prototype instead of a premium product. iOS reads shadow* props directly; Android needs the
// separate `elevation` number (shadowColor/opacity are ignored there pre-tinted-elevation APIs).
export const shadows = {
  card: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.28,
    shadowRadius: 20,
    elevation: 6,
  },
  glow: (color: string) => ({
    shadowColor: color,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  }),
};

export const tokens = { colors, gradients, map, motion, spacing, fontSize, typography, radii, shadows };
export default tokens;
