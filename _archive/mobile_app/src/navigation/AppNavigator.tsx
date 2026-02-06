/**
 * Main App Navigation
 * Handles authenticated and unauthenticated states
 */

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createDrawerNavigator} from '@react-navigation/drawer';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Screens
import {LoginScreen} from '../screens/auth/LoginScreen';
import {DashboardScreen} from '../screens/dashboard/DashboardScreen';
import {LeadsScreen} from '../screens/leads/LeadsScreen';
import {LeadDetailScreen} from '../screens/leads/LeadDetailScreen';
import {PropertiesScreen} from '../screens/properties/PropertiesScreen';
import {PropertyDetailScreen} from '../screens/properties/PropertyDetailScreen';
import {PropertySwipeScreen} from '../screens/properties/PropertySwipeScreen';
import {AnalyticsScreen} from '../screens/analytics/AnalyticsScreen';
import {SettingsScreen} from '../screens/settings/SettingsScreen';
import {NotificationsScreen} from '../screens/notifications/NotificationsScreen';
import {CameraScreen} from '../screens/camera/CameraScreen';
import {VoiceNoteScreen} from '../screens/voice/VoiceNoteScreen';

// Hooks and utilities
import {useAuth} from '../hooks/useAuth';
import {theme} from '../theme/theme';

// Navigation types
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  ForgotPassword: undefined;
  Register: undefined;
};

export type MainTabParamList = {
  Dashboard: undefined;
  Leads: undefined;
  Properties: undefined;
  Analytics: undefined;
  More: undefined;
};

export type LeadsStackParamList = {
  LeadsList: undefined;
  LeadDetail: {leadId: string};
  VoiceNote: {leadId: string};
};

export type PropertiesStackParamList = {
  PropertiesList: undefined;
  PropertyDetail: {propertyId: string};
  PropertySwipe: {leadId?: string};
  Camera: {context: 'property' | 'lead'; entityId: string};
};

// Stack Navigators
const RootStack = createStackNavigator<RootStackParamList>();
const AuthStack = createStackNavigator<AuthStackParamList>();
const MainTab = createBottomTabNavigator<MainTabParamList>();
const LeadsStack = createStackNavigator<LeadsStackParamList>();
const PropertiesStack = createStackNavigator<PropertiesStackParamList>();
const Drawer = createDrawerNavigator();

// Auth Navigator
const AuthNavigator: React.FC = () => {
  return (
    <AuthStack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: {backgroundColor: theme.colors.background},
      }}>
      <AuthStack.Screen name="Login" component={LoginScreen} />
    </AuthStack.Navigator>
  );
};

// Leads Stack Navigator
const LeadsNavigator: React.FC = () => {
  return (
    <LeadsStack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.primary,
        },
        headerTintColor: theme.colors.white,
        headerTitleStyle: {
          fontFamily: theme.fonts.semiBold,
        },
      }}>
      <LeadsStack.Screen
        name="LeadsList"
        component={LeadsScreen}
        options={{
          title: 'Leads',
          headerRight: () => (
            <Icon
              name="notifications"
              size={24}
              color={theme.colors.white}
              style={{marginRight: 15}}
            />
          ),
        }}
      />
      <LeadsStack.Screen
        name="LeadDetail"
        component={LeadDetailScreen}
        options={{title: 'Lead Details'}}
      />
      <LeadsStack.Screen
        name="VoiceNote"
        component={VoiceNoteScreen}
        options={{title: 'Voice Note'}}
      />
    </LeadsStack.Navigator>
  );
};

// Properties Stack Navigator
const PropertiesNavigator: React.FC = () => {
  return (
    <PropertiesStack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.primary,
        },
        headerTintColor: theme.colors.white,
        headerTitleStyle: {
          fontFamily: theme.fonts.semiBold,
        },
      }}>
      <PropertiesStack.Screen
        name="PropertiesList"
        component={PropertiesScreen}
        options={{
          title: 'Properties',
          headerRight: () => (
            <Icon
              name="search"
              size={24}
              color={theme.colors.white}
              style={{marginRight: 15}}
            />
          ),
        }}
      />
      <PropertiesStack.Screen
        name="PropertyDetail"
        component={PropertyDetailScreen}
        options={{title: 'Property Details'}}
      />
      <PropertiesStack.Screen
        name="PropertySwipe"
        component={PropertySwipeScreen}
        options={{title: 'Find Matches'}}
      />
      <PropertiesStack.Screen
        name="Camera"
        component={CameraScreen}
        options={{title: 'Camera'}}
      />
    </PropertiesStack.Navigator>
  );
};

// Main Tab Navigator
const MainTabNavigator: React.FC = () => {
  return (
    <MainTab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName = 'home';

          switch (route.name) {
            case 'Dashboard':
              iconName = 'dashboard';
              break;
            case 'Leads':
              iconName = 'people';
              break;
            case 'Properties':
              iconName = 'location-city';
              break;
            case 'Analytics':
              iconName = 'bar-chart';
              break;
            case 'More':
              iconName = 'menu';
              break;
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          paddingBottom: 5,
          height: 60,
        },
        tabBarLabelStyle: {
          fontFamily: theme.fonts.medium,
          fontSize: 12,
        },
        headerShown: false,
      })}>
      <MainTab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{title: 'Dashboard'}}
      />
      <MainTab.Screen
        name="Leads"
        component={LeadsNavigator}
        options={{title: 'Leads'}}
      />
      <MainTab.Screen
        name="Properties"
        component={PropertiesNavigator}
        options={{title: 'Properties'}}
      />
      <MainTab.Screen
        name="Analytics"
        component={AnalyticsScreen}
        options={{title: 'Analytics'}}
      />
      <MainTab.Screen
        name="More"
        component={SettingsScreen}
        options={{title: 'More'}}
      />
    </MainTab.Navigator>
  );
};

// Main App Navigator
export const AppNavigator: React.FC = () => {
  const {isAuthenticated} = useAuth();

  return (
    <RootStack.Navigator screenOptions={{headerShown: false}}>
      {isAuthenticated ? (
        <RootStack.Screen name="Main" component={MainTabNavigator} />
      ) : (
        <RootStack.Screen name="Auth" component={AuthNavigator} />
      )}
    </RootStack.Navigator>
  );
};