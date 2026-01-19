/**
 * GHL Real Estate AI Mobile App
 * Root Application Component
 */

import React, {useEffect} from 'react';
import {StatusBar, StyleSheet} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {Provider} from 'react-redux';
import {PersistGate} from 'redux-persist/integration/react';

import {store, persistor} from './store/store';
import {AppNavigator} from './navigation/AppNavigator';
import {SplashScreen} from './components/SplashScreen';
import {ErrorBoundary} from './components/ErrorBoundary';
import {NotificationService} from './services/NotificationService';
import {AuthService} from './services/AuthService';
import {SyncService} from './services/SyncService';
import {theme} from './theme/theme';

const App: React.FC = () => {
  useEffect(() => {
    // Initialize services
    const initializeApp = async () => {
      try {
        // Initialize notification service
        await NotificationService.initialize();

        // Initialize auth service
        await AuthService.initialize();

        // Initialize sync service
        await SyncService.initialize();

        // Request permissions
        await requestPermissions();

        console.log('App initialized successfully');
      } catch (error) {
        console.error('App initialization failed:', error);
      }
    };

    initializeApp();
  }, []);

  const requestPermissions = async () => {
    try {
      // Request notification permissions
      await NotificationService.requestPermissions();

      // Request location permissions
      // await LocationService.requestPermissions();

      // Request camera permissions (for property photos)
      // await CameraService.requestPermissions();

    } catch (error) {
      console.warn('Permission request failed:', error);
    }
  };

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <PersistGate loading={<SplashScreen />} persistor={persistor}>
          <NavigationContainer theme={theme.navigation}>
            <StatusBar
              barStyle="dark-content"
              backgroundColor={theme.colors.background}
            />
            <AppNavigator />
          </NavigationContainer>
        </PersistGate>
      </Provider>
    </ErrorBoundary>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;