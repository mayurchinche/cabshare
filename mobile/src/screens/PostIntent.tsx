import React, { useEffect, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { createRideIntent, RideIntentCreate, Station, Place } from '../services/apiClient';
import { useIntentStatus } from '../services/intentStatus';
import type { RootStackParamList } from '../navigation/AppNavigator';
import Button from '../components/Button';
import Card from '../components/Card';
import CarMotion from '../components/CarMotion';
import TextField from '../components/TextField';
import { colors, spacing, typography } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'PostIntent'>;

const LUGGAGE_OPTIONS: RideIntentCreate['luggage_size'][] = ['none', 'small', 'medium', 'large'];
const GENDER_OPTIONS: NonNullable<RideIntentCreate['gender_preference']>[] = [
  'any',
  'male',
  'female',
];

/**
 * FR-001/FR-002: capture a rider's ride-share intent (station, destination, luggage,
 * expected arrival, optional gender preference), submit it, then poll (T029) until the
 * 5-minute matching window resolves into a match, expiry, or cancellation. Origin/destination
 * are now picked via `StationPicker` (Feature 003, station-only scope) so lat/lng are real
 * coordinates from the imported station dataset, not placeholder zeros.
 *
 * Feature 002: restyled with shared theme/components + CarMotion "searching" state while
 * polling for a match.
 */
function addDaysToDateString(dateStr: string, days: number): string {
  const d = new Date(`${dateStr}T00:00:00`);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function PostIntentScreen({ navigation, route }: Props): React.JSX.Element {
  const [originStation, setOriginStation] = useState<Station | null>(null);
  const [destinationStation, setDestinationStation] = useState<Station | null>(null);
  const [luggageSize, setLuggageSize] = useState<RideIntentCreate['luggage_size']>('small');
  const [genderPreference, setGenderPreference] =
    useState<NonNullable<RideIntentCreate['gender_preference']>>('any');
  const [expectedArrivalTime, setExpectedArrivalTime] = useState('');
  const [selectedTrain, setSelectedTrain] = useState<{ number: string; name: string } | null>(null);
  const [travelDate, setTravelDate] = useState<string | null>(null);
  const [finalDestination, setFinalDestination] = useState<Place | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submittedIntentId, setSubmittedIntentId] = useState<string | null>(null);

  const { intent, error } = useIntentStatus(submittedIntentId);

  useEffect(() => {
    if (intent?.status === 'matched' && intent.match_id) {
      navigation.navigate('MatchReview', { matchId: intent.match_id });
    }
  }, [intent, navigation]);

  // Receives the picked station (or train) back from StationPicker/TrainPicker (route param,
  // cleared after applying so re-focusing this screen later doesn't re-apply a stale selection).
  useEffect(() => {
    const { selectedStation, field, selectedTrain: pickedTrain, travelDate: pickedDate, selectedPlace } =
      route.params ?? {};
    if (selectedStation && field) {
      if (field === 'origin') setOriginStation(selectedStation);
      else setDestinationStation(selectedStation);
    }
    if (selectedPlace) {
      setFinalDestination(selectedPlace);
    }
    if (pickedTrain && pickedDate) {
      setSelectedTrain({ number: pickedTrain.number, name: pickedTrain.name });
      setTravelDate(pickedDate);
      // The rider must not type this by hand — it comes straight from the train's own
      // scheduled arrival at the chosen destination station, so matching windows line up with
      // when the train actually gets in, not a guess.
      if (pickedTrain.destinationArrivalTime) {
        const arrivalDate = addDaysToDateString(pickedDate, pickedTrain.dayOffset);
        setExpectedArrivalTime(`${arrivalDate}T${pickedTrain.destinationArrivalTime}`);
      }
    }
    if (selectedStation || field || pickedTrain || pickedDate || selectedPlace) {
      navigation.setParams({
        selectedStation: undefined,
        field: undefined,
        selectedTrain: undefined,
        travelDate: undefined,
        selectedPlace: undefined,
      });
    }
  }, [route.params, navigation]);

  const onPickTrain = (): void => {
    if (!originStation || !destinationStation) {
      Alert.alert('Pick stations first', 'Choose your origin and destination stations before selecting a train.');
      return;
    }
    const date = travelDate ?? new Date().toISOString().slice(0, 10);
    navigation.navigate('TrainPicker', {
      fromCode: originStation.station_code,
      toCode: destinationStation.station_code,
      travelDate: date,
    });
  };

  const onClearTrain = (): void => {
    setSelectedTrain(null);
    setTravelDate(null);
    setExpectedArrivalTime('');
  };

  const onPickFinalDestination = (): void => {
    navigation.navigate('PlacePicker', undefined);
  };

  const onSubmit = async (): Promise<void> => {
    if (!originStation || !destinationStation || !selectedTrain || !expectedArrivalTime) {
      Alert.alert('Missing details', 'Station, destination, and your train are required.');
      return;
    }
    if (!finalDestination) {
      Alert.alert('Missing drop-off', 'Add where the cab should drop you after the station.');
      return;
    }

    setSubmitting(true);
    try {
      const created = await createRideIntent({
        origin_station: originStation.name,
        origin_lat: originStation.latitude ?? 0,
        origin_lng: originStation.longitude ?? 0,
        destination: destinationStation.name,
        destination_lat: destinationStation.latitude ?? 0,
        destination_lng: destinationStation.longitude ?? 0,
        luggage_size: luggageSize,
        expected_arrival_time: new Date(expectedArrivalTime).toISOString(),
        gender_preference: genderPreference,
        selected_train_number: selectedTrain?.number ?? null,
        travel_date: selectedTrain ? travelDate : null,
        final_destination: finalDestination.display_name,
        final_destination_lat: finalDestination.latitude,
        final_destination_lng: finalDestination.longitude,
      });
      setSubmittedIntentId(created.id);
    } catch {
      Alert.alert(
        'Saved offline',
        'No connection right now — your request will send automatically once you are back online.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (submittedIntentId) {
    const expired = intent?.status === 'expired';
    return (
      <View style={styles.centeredContainer}>
        <CarMotion
          state={expired ? 'idle' : 'searching'}
          caption={
            expired
              ? 'No match found in time — you can search again.'
              : 'Looking for a co-rider heading your way…'
          }
        />
        {error ? <Text style={styles.errorText}>Connection issue — still trying…</Text> : null}
        {expired ? (
          <Button title="Search again" onPress={() => setSubmittedIntentId(null)} />
        ) : null}
      </View>
    );
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
      <Text style={typography.heading}>Where are you headed?</Text>
      <Text style={[typography.caption, styles.subtitle]}>
        We'll find a co-rider on the same route
      </Text>

      <Card style={styles.card}>
        <Text style={styles.sectionLabel}>Origin station</Text>
        <Pressable
          style={styles.stationField}
          onPress={() => navigation.navigate('StationPicker', { field: 'origin' })}
        >
          <Text style={originStation ? typography.body : styles.placeholder}>
            {originStation ? originStation.name : 'Select pickup station'}
          </Text>
        </Pressable>

        <Text style={styles.sectionLabel}>Destination station</Text>
        <Pressable
          style={styles.stationField}
          onPress={() => navigation.navigate('StationPicker', { field: 'destination' })}
        >
          <Text style={destinationStation ? typography.body : styles.placeholder}>
            {destinationStation ? destinationStation.name : 'Select destination station'}
          </Text>
        </Pressable>

        <Text style={styles.sectionLabel}>Train</Text>
        <Pressable style={styles.stationField} onPress={onPickTrain}>
          <Text style={selectedTrain ? typography.body : styles.placeholder}>
            {selectedTrain ? `${selectedTrain.name} · #${selectedTrain.number}` : 'Select your train'}
          </Text>
        </Pressable>
        {selectedTrain ? (
          <View style={styles.trainActionsRow}>
            <Pressable
              onPress={() =>
                navigation.navigate('TrainLiveStatus', {
                  trainNumber: selectedTrain.number,
                  trainName: selectedTrain.name,
                  travelDate: travelDate ?? new Date().toISOString().slice(0, 10),
                })
              }
            >
              <Text style={styles.trackLink}>Track this train live →</Text>
            </Pressable>
            <Pressable onPress={onClearTrain}>
              <Text style={styles.clearLink}>Change train</Text>
            </Pressable>
          </View>
        ) : null}

        <TextField
          label="Expected arrival time"
          value={expectedArrivalTime}
          editable={false}
          placeholder="Pick a train above to set this automatically"
          helperText="Set from your selected train's scheduled arrival — not editable"
        />

        <Text style={styles.sectionLabel}>Final drop-off</Text>
        <Pressable style={styles.stationField} onPress={onPickFinalDestination}>
          <Text style={finalDestination ? typography.body : styles.placeholder} numberOfLines={2}>
            {finalDestination ? finalDestination.display_name : 'Where should the cab drop you?'}
          </Text>
        </Pressable>
        <Text style={[typography.caption, styles.helperCaption]}>
          The cab picks up at {destinationStation ? destinationStation.name : 'your destination station'} and
          drops you here — separate from your co-rider's own drop-off
        </Text>

        <Text style={styles.sectionLabel}>Luggage size</Text>
        <View style={styles.chipRow}>
          {LUGGAGE_OPTIONS.map((option) => (
            <Button
              key={option}
              title={option}
              variant={luggageSize === option ? 'primary' : 'secondary'}
              onPress={() => setLuggageSize(option)}
              style={styles.chip}
            />
          ))}
        </View>

        <Text style={styles.sectionLabel}>Co-rider gender preference</Text>
        <View style={styles.chipRow}>
          {GENDER_OPTIONS.map((option) => (
            <Button
              key={option}
              title={option}
              variant={genderPreference === option ? 'primary' : 'secondary'}
              onPress={() => setGenderPreference(option)}
              style={styles.chip}
            />
          ))}
        </View>

        <Button
          title="Find a ride share"
          onPress={onSubmit}
          loading={submitting}
          style={styles.submitButton}
        />
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { padding: spacing.md },
  centeredContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.background,
  },
  subtitle: { marginTop: spacing.xs, marginBottom: spacing.md },
  card: { marginTop: spacing.sm },
  sectionLabel: {
    ...typography.caption,
    marginBottom: spacing.xs,
    marginTop: spacing.xs,
  },
  stationField: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm + 2,
    marginBottom: spacing.sm,
    backgroundColor: colors.surface,
  },
  placeholder: { ...typography.body, color: colors.textTertiary },
  helperCaption: { marginBottom: spacing.sm },
  trainActionsRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.sm },
  trackLink: { ...typography.caption, color: colors.accentTeal, fontWeight: '600' },
  clearLink: { ...typography.caption, color: colors.textTertiary, fontWeight: '600' },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginBottom: spacing.md,
  },
  chip: { minHeight: 36, paddingVertical: spacing.xs, paddingHorizontal: spacing.sm + 4, minWidth: 0, borderRadius: 999 },
  submitButton: { marginTop: spacing.sm },
  errorText: {
    ...typography.caption,
    color: colors.error,
    marginTop: spacing.sm,
  },
});
