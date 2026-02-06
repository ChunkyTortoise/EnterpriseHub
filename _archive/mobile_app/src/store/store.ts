/**
 * Redux Store Configuration
 * Handles state management with persistence
 */

import {configureStore} from '@reduxjs/toolkit';
import {persistStore, persistReducer} from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {combineReducers} from '@reduxjs/toolkit';

// Reducers
import authReducer from './slices/authSlice';
import leadsReducer from './slices/leadsSlice';
import propertiesReducer from './slices/propertiesSlice';
import notificationsReducer from './slices/notificationsSlice';
import syncReducer from './slices/syncSlice';
import settingsReducer from './slices/settingsSlice';
import analyticsReducer from './slices/analyticsSlice';

// Persist config
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'settings'], // Only persist auth and settings
};

const syncPersistConfig = {
  key: 'sync',
  storage: AsyncStorage,
  whitelist: ['pendingOperations', 'lastSyncTime'], // Persist offline operations
};

const rootReducer = combineReducers({
  auth: authReducer,
  leads: leadsReducer,
  properties: propertiesReducer,
  notifications: notificationsReducer,
  sync: persistReducer(syncPersistConfig, syncReducer),
  settings: settingsReducer,
  analytics: analyticsReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: getDefaultMiddleware =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          'persist/PERSIST',
          'persist/REHYDRATE',
          'persist/PAUSE',
          'persist/PURGE',
          'persist/REGISTER',
          'persist/FLUSH',
        ],
      },
    }),
  devTools: __DEV__, // Enable Redux DevTools in development
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;