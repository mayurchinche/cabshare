import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Text, TextInput, View, StyleSheet, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../navigation/AppNavigator';
import { searchStations, Station } from '../services/apiClient';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'StationPicker'>;

/**
 * Feature 003 (station-picker-only scope): real station search over the free `datameet/railways`
 * import (`api/scripts/seed_stations.py`, ~9k stations) — replaces free-text origin/destination
 * typing in `PostIntent` with an actual autocomplete list, so ride requests carry real
 * lat/lng instead of placeholder zeros.
 */
export default function StationPickerScreen({ route, navigation }: Props): React.JSX.Element {
  const { field } = route.params;
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Station[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    const timer = setTimeout(() => {
      searchStations(query)
        .then((stations) => {
          if (!cancelled) setResults(stations);
        })
        .catch(() => {
          if (!cancelled) setResults([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 250); // debounce so every keystroke doesn't fire a request
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  const onSelect = (station: Station): void => {
    navigation.navigate({
      name: 'PostIntent',
      params: { selectedStation: station, field },
      merge: true,
    });
  };

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <View style={styles.container}>
        <Text style={typography.heading}>
          {field === 'origin' ? 'Pickup station' : 'Destination station'}
        </Text>
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={setQuery}
          placeholder="Search by name or code (e.g. Pune, NDLS)"
          placeholderTextColor={colors.textTertiary}
          autoFocus
        />
        {loading ? <ActivityIndicator color={colors.primary} style={styles.loader} /> : null}
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          keyboardShouldPersistTaps="handled"
          renderItem={({ item }) => (
            <Pressable style={styles.row} onPress={() => onSelect(item)}>
              <Text style={typography.body}>{item.name}</Text>
              <Text style={typography.caption}>
                {item.station_code}
                {item.state ? ` · ${item.state}` : ''}
              </Text>
            </Pressable>
          )}
          ListEmptyComponent={
            query.trim().length >= 2 && !loading ? (
              <Text style={[typography.caption, styles.empty]}>No stations found</Text>
            ) : null
          }
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { flex: 1, padding: spacing.md },
  input: {
    marginTop: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
  },
  loader: { marginVertical: spacing.sm },
  row: {
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  empty: { textAlign: 'center', marginTop: spacing.lg },
});
