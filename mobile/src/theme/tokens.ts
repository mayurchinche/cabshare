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
  primary: '#8B7CF6', // accent-violet, used as solid fallback where a gradient can't render
  primaryPressed: '#7A6BE0',
  secondary: '#12141B',
  accent: '#F5C451', // accent-gold
  accentTeal: '#00D9C6',
  accentViolet: '#8B7CF6',
  textPrimary: '#F5F6FA',
  textSecondary: '#9AA1B2',
  textTertiary: '#5C6273',
  borderFocused: '#00D9C6',
  error: '#F87171',
  success: '#34D399',
  warning: '#FBBF24',
};

/** Gradient stop pairs for `expo-linear-gradient`, matching `--grad-primary`/`--grad-gold`. */
export const gradients = {
  primary: ['#6C5CE7', '#00D9C6'] as const,
  gold: ['#F5C451', '#F79A3C'] as const,
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

export const typography = {
  heading: { fontSize: 24, fontWeight: '700' as const, color: colors.textPrimary, letterSpacing: -0.3 },
  subheading: { fontSize: 17, fontWeight: '600' as const, color: colors.textPrimary, letterSpacing: -0.1 },
  body: { fontSize: 15, fontWeight: '400' as const, color: colors.textPrimary },
  caption: { fontSize: 13, fontWeight: '400' as const, color: colors.textSecondary },
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

export const tokens = { colors, gradients, spacing, typography, radii, shadows };
export default tokens;
