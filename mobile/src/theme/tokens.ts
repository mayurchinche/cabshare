/**
 * Shared design tokens (Feature 004: CRED/INDMoney-tier premium dark theme). Values map 1:1 to
 * `specs/004-full-app-experience/mockups/design-system.css` (the signed-off visual reference) —
 * every screen/component MUST import from here instead of hardcoding colors/spacing/type, so
 * changing the palette never means hunting through every screen file.
 */
export const colors = {
  background: '#05060A',
  surface: '#12141B', // ponytail: opaque stand-in for the mockup's blurred glass card — real
  // backdrop blur needs a BlurView layered behind content on a per-card basis; against this flat
  // dark background the visual difference is negligible, so skip until a busier background
  // (photo/map) actually needs it.
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
  heading: { fontSize: 24, fontWeight: '700' as const, color: colors.textPrimary },
  subheading: { fontSize: 17, fontWeight: '600' as const, color: colors.textPrimary },
  body: { fontSize: 15, fontWeight: '400' as const, color: colors.textPrimary },
  caption: { fontSize: 13, fontWeight: '400' as const, color: colors.textSecondary },
};

export const radii = {
  sm: 10,
  md: 16,
  lg: 24,
};

export const tokens = { colors, gradients, spacing, typography, radii };
export default tokens;
