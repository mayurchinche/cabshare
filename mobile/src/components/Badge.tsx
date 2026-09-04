import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { colors } from '../theme';

type BadgeStatus = 'verified' | 'pending' | 'rejected';

const BADGE_COLORS: Record<BadgeStatus, { bg: string; text: string }> = {
  verified: { bg: 'rgba(52,211,153,0.15)', text: colors.success },
  pending: { bg: 'rgba(251,191,36,0.15)', text: colors.warning },
  rejected: { bg: 'rgba(248,113,113,0.15)', text: colors.error },
};

type Props = {
  status: BadgeStatus;
  label: string;
};

/** Pill status badge — matches `design-system.css`'s `.badge.verified/.pending/.rejected`. */
export default function Badge({ status, label }: Props): React.JSX.Element {
  const { bg, text } = BADGE_COLORS[status];
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.text, { color: text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
  },
  text: {
    fontSize: 11,
    fontWeight: '700',
  },
});
