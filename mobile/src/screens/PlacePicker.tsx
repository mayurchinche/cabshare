import React, { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Text, TextInput, View, StyleSheet, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../navigation/AppNavigator';
import { searchPlaces, Place } from '../services/apiClient';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'PlacePicker'>;

/**
 * "Where are you actually going?" — the rider's exact final drop-off (home/office/hotel), a real
 * cab-app-style address search over free OpenStreetMap data. Distinct from `StationPicker`: this
 * is the point the *cab* drops the rider at, once both matched riders' trains land at the shared
 * destination station.
 */
export default function PlacePickerScreen({ navigation }: Props): React.JSX.Element {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (query.trim().length < 3) {
      setResults([]);
      return;
    }
    setLoading(true);
    const timer = setTimeout(() => {
      searchPlaces(query)
        .then((places) => {
          if (!cancelled) setResults(places);
        })
        .catch(() => {
          if (!cancelled) setResults([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 350); // Nominatim's fair-use policy asks for ~1 req/sec; debounce a bit more than stations
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  const onSelect = (place: Place): void => {
    navigation.navigate({
      name: 'PostIntent',
      params: { selectedPlace: place },
      merge: true,
    });
  };

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <View style={styles.container}>
        <Text style={typography.heading}>Your final drop-off</Text>
        <Text style={[typography.caption, styles.subtitle]}>
          Where the cab drops you after the shared station — home, office, or any address
        </Text>
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={setQuery}
          placeholder="Search an address, area, or landmark"
          placeholderTextColor={colors.textTertiary}
          autoFocus
        />
        {loading ? <ActivityIndicator color={colors.primary} style={styles.loader} /> : null}
        <FlatList
          data={results}
          keyExtractor={(item, index) => `${item.latitude},${item.longitude},${index}`}
          keyboardShouldPersistTaps="handled"
          renderItem={({ item }) => (
            <Pressable style={styles.row} onPress={() => onSelect(item)}>
              <Text style={typography.body}>{item.display_name}</Text>
            </Pressable>
          )}
          ListEmptyComponent={
            query.trim().length >= 3 && !loading ? (
              <Text style={[typography.caption, styles.empty]}>No matching places found</Text>
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
  subtitle: { marginTop: spacing.xs },
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
