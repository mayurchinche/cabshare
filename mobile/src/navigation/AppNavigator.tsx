import React from 'react';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import Ionicons from '@expo/vector-icons/Ionicons';

import SplashScreen from '../screens/Splash';
import VerificationScreen from '../screens/Verification';
import PanKycScreen from '../screens/PanKyc';
import ProfileSetupScreen from '../screens/ProfileSetup';
import HomeScreen from '../screens/Home';
import PostIntentScreen from '../screens/PostIntent';
import StationPickerScreen from '../screens/StationPicker';
import TrainPickerScreen from '../screens/TrainPicker';
import PlacePickerScreen from '../screens/PlacePicker';
import TrainLiveStatusScreen from '../screens/TrainLiveStatus';
import MatchReviewScreen from '../screens/MatchReview';
import RideConfirmScreen from '../screens/RideConfirm';
import CancelScreen from '../screens/Cancel';
import RideHistoryListScreen from '../screens/RideHistoryList';
import RideHistoryDetailScreen from '../screens/RideHistoryDetail';
import ProfileAccountScreen from '../screens/ProfileAccount';
import { colors } from '../theme';

/** Feature 004: dark nav theme so screen-transition backgrounds and native headers match the
 * CRED/INDMoney-tier palette instead of React Navigation's light default. */
const navTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.background,
    card: colors.surfaceSolid,
    text: colors.textPrimary,
    border: colors.border,
    primary: colors.accentTeal,
  },
};

export type HomeTabParamList = {
  HomeTab: undefined;
  HistoryTab: undefined;
  ProfileTab: undefined;
};

export type RootStackParamList = {
  Splash: undefined;
  Verification: undefined;
  PanKyc: { riderId: string };
  ProfileSetup: { riderId: string; mode?: 'edit'; initialName?: string; initialGender?: 'male' | 'female' | 'other' | 'undisclosed' };
  Home: undefined;
  PostIntent: {
    selectedStation?: import('../services/apiClient').Station;
    field?: 'origin' | 'destination';
    selectedTrain?: { number: string; name: string; destinationArrivalTime: string | null; dayOffset: number };
    travelDate?: string;
    selectedPlace?: import('../services/apiClient').Place;
  } | undefined;
  StationPicker: { field: 'origin' | 'destination' };
  TrainPicker: { fromCode: string; toCode: string; travelDate: string };
  PlacePicker: undefined;
  TrainLiveStatus: { trainNumber: string; trainName?: string; travelDate: string };
  MatchReview: { matchId: string };
  RideConfirm: { rideId: string; matchId: string };
  Cancel: { rideId: string };
  RideHistoryDetail: { rideId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<HomeTabParamList>();

const TAB_ICON: Record<keyof HomeTabParamList, { active: keyof typeof Ionicons.glyphMap; inactive: keyof typeof Ionicons.glyphMap }> = {
  HomeTab: { active: 'home', inactive: 'home-outline' },
  HistoryTab: { active: 'time', inactive: 'time-outline' },
  ProfileTab: { active: 'person-circle', inactive: 'person-circle-outline' },
};

/** Feature 004: bottom tab shell for the post-login app (Home/History/Profile), nested inside
 * the root stack so onboarding screens and detail/flow screens (MatchReview, RideConfirm, etc.)
 * can still push full-screen on top of it. */
function HomeTabs(): React.JSX.Element {
  return (
    <Tab.Navigator
      screenOptions={({ route }: { route: { name: keyof HomeTabParamList } }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.accentTeal,
        tabBarInactiveTintColor: colors.textTertiary,
        tabBarStyle: {
          backgroundColor: 'rgba(10,11,14,0.95)',
          borderTopColor: colors.border,
        },
        tabBarIcon: ({ focused, color }: { focused: boolean; color: string }) => (
          <Ionicons name={focused ? TAB_ICON[route.name].active : TAB_ICON[route.name].inactive} size={22} color={color} />
        ),
      })}
    >
      <Tab.Screen name="HomeTab" component={HomeScreen} options={{ title: 'Home' }} />
      <Tab.Screen name="HistoryTab" component={RideHistoryListScreen} options={{ title: 'History' }} />
      <Tab.Screen name="ProfileTab" component={ProfileAccountScreen} options={{ title: 'Profile' }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator(): React.JSX.Element {
  return (
    // GestureHandlerRootView must be the OUTERMOST view of the app — @gorhom/bottom-sheet's pan
    // gestures are silently dead (sheet renders but won't drag) if any gesture-handler consumer
    // mounts outside it. Wrapping here rather than in index.js keeps it colocated with the
    // navigation tree it protects.
    <GestureHandlerRootView style={{ flex: 1 }}>
    <SafeAreaProvider>
    <NavigationContainer theme={navTheme}>
      <Stack.Navigator
        initialRouteName="Splash"
        screenOptions={{
          headerShown: false,
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.textPrimary,
          headerShadowVisible: false,
        }}
      >
        <Stack.Screen name="Splash" component={SplashScreen} />
        <Stack.Screen name="Verification" component={VerificationScreen} />
        <Stack.Screen name="PanKyc" component={PanKycScreen} />
        <Stack.Screen name="ProfileSetup" component={ProfileSetupScreen} />
        <Stack.Screen name="Home" component={HomeTabs} />
        <Stack.Screen
          name="PostIntent"
          component={PostIntentScreen}
          options={{ headerShown: true, title: 'New ride request' }}
        />
        <Stack.Screen
          name="StationPicker"
          component={StationPickerScreen}
          options={{ headerShown: true, title: 'Choose a station' }}
        />
        <Stack.Screen
          name="TrainPicker"
          component={TrainPickerScreen}
          options={{ headerShown: true, title: 'Choose a train' }}
        />
        <Stack.Screen
          name="PlacePicker"
          component={PlacePickerScreen}
          options={{ headerShown: true, title: 'Final drop-off' }}
        />
        <Stack.Screen
          name="TrainLiveStatus"
          component={TrainLiveStatusScreen}
          options={{ headerShown: true, title: 'Live train status' }}
        />
        <Stack.Screen
          name="MatchReview"
          component={MatchReviewScreen}
          options={{ headerShown: true, title: 'Match found' }}
        />
        <Stack.Screen
          name="RideConfirm"
          component={RideConfirmScreen}
          options={{ headerShown: true, title: 'Ride' }}
        />
        <Stack.Screen name="Cancel" component={CancelScreen} options={{ headerShown: true, title: 'Cancel ride' }} />
        <Stack.Screen
          name="RideHistoryDetail"
          component={RideHistoryDetailScreen}
          options={{ headerShown: true, title: 'Ride details' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
    </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
