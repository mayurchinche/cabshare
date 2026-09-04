/**
 * @format
 */
import { registerRootComponent } from 'expo';
import AppNavigator from './src/navigation/AppNavigator';

// ponytail: AppNavigator already wraps NavigationContainer, so it doubles as the root
// component — no separate App.tsx needed. registerRootComponent (instead of
// AppRegistry.registerComponent) is what lets Expo Go pick this app up.
registerRootComponent(AppNavigator);
