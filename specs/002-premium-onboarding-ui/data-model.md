# Data Model: Premium UI/UX Across the Full App Journey

This feature has no persisted data entities (no database/API changes — see spec Key Entities,
which are all presentation-layer constructs). Documented here as TypeScript shapes for the
shared component contracts instead of DB tables.

## DesignTokens (`mobile/src/theme/tokens.ts`)

```ts
type DesignTokens = {
  colors: {
    primary: string; primaryPressed: string; secondary: string; accent: string;
    background: string; surface: string; textPrimary: string; textSecondary: string;
    border: string; borderFocused: string; error: string; success: string; warning: string;
  };
  spacing: { xs: number; sm: number; md: number; lg: number; xl: number };
  typography: {
    heading: { fontSize: number; fontWeight: string };
    body: { fontSize: number; fontWeight: string };
    caption: { fontSize: number; fontWeight: string };
  };
  radii: { sm: number; md: number; lg: number };
};
```

**Validation rules**: Every new/restyled component MUST import from this single module — no
component may hardcode a hex color, font size, or spacing value inline (this is how FR-001/FR-007
are enforced in code review, not just by convention).

## MotionMotif (`CarMotion` component props)

```ts
type CarMotionProps = {
  variant: 'idle' | 'success';
  reduceMotionOverride?: boolean; // for testing; production reads AccessibilityInfo
};
```

**State transitions**: `idle` (looping, shown on Verification/PostIntent while waiting) →
`success` (one-shot, shown after OTP confirm / Ride Confirm) — never the reverse within a single
screen's lifecycle.

## Shared component prop contracts (summary)

| Component | Key props | FR reference |
|---|---|---|
| `Button` | `variant: 'primary'\|'secondary'\|'destructive'`, `state: 'default'\|'pressed'\|'disabled'\|'loading'` | FR-009 |
| `TextField` | `state: 'default'\|'focused'\|'error'`, `errorMessage?: string` | FR-002, FR-006 |
| `SegmentedCodeInput` | `length: number`, `value: string`, `onChange`, `error?: boolean` | FR-003, FR-006 |
| `Card` | `variant: 'default'\|'match'\|'destructive'` | FR-010 |
| `EmptyState` | `title: string`, `body: string`, `icon?: ReactNode` | FR-010 |
