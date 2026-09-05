import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { colors } from '../theme';

type BadgeStatus = 'verified' | 'pending' | 'rejected';

const BADGE_COLORS: Record<BadgeStatus, { bg: string; text: string; border: string }> = {
  verified: { bg: 'rgba(52,211,153,0.15)', text: colors.success, border: 'rgba(52,211,153,0.35)' },
  pending: { bg: 'rgba(251,191,36,0.15)', text: colors.warning, border: 'rgba(251,191,36,0.35)' },
  rejected: { bg: 'rgba(248,113,113,0.15)', text: colors.error, border: 'rgba(248,113,113,0.35)' },
};

type Props = {
  status: BadgeStatus;
  label: string;
};

/** Pill status badge — matches `design-system.css`'s `.badge.verified/.pending/.rejected`. */
export default function Badge({ status, label }: Props): React.JSX.Element {
  const { bg, text, border } = BADGE_COLORS[status];
  return (
    <View style={[styles.badge, { backgroundColor: bg, borderColor: border }]}>
      <Text style={[styles.text, { color: text }]}>{label.toUpperCase()}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: 1,
  },
  text: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.6,
  },
});
