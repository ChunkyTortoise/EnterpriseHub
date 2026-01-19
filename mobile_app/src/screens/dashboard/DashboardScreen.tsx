/**
 * Dashboard Screen - Main app dashboard
 * Shows key metrics, quick actions, and real-time updates
 */

import React, {useEffect, useState, useCallback} from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
  Dimensions,
} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';

// Components
import {Header} from '../../components/Header';
import {MetricCard} from '../../components/MetricCard';
import {QuickActionGrid} from '../../components/QuickActionGrid';
import {RecentActivity} from '../../components/RecentActivity';
import {NotificationBanner} from '../../components/NotificationBanner';
import {LoadingSpinner} from '../../components/LoadingSpinner';
import {ErrorMessage} from '../../components/ErrorMessage';

// Services and hooks
import {ApiService, MobileDashboard} from '../../services/ApiService';
import {SyncService} from '../../services/SyncService';
import {NotificationService} from '../../services/NotificationService';
import {useAppDispatch, useAppSelector} from '../../hooks/redux';
import {setDashboardData, setLoading, setError} from '../../store/slices/dashboardSlice';

// Theme
import {theme} from '../../theme/theme';

const {width} = Dimensions.get('window');

export const DashboardScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const {dashboardData, isLoading, error} = useAppSelector(state => state.dashboard);
  const {user} = useAppSelector(state => state.auth);

  const [refreshing, setRefreshing] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);

  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    try {
      dispatch(setLoading(true));
      const data = await ApiService.getDashboard();
      dispatch(setDashboardData(data));

      // Trigger background sync
      SyncService.triggerBackgroundSync();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard';
      dispatch(setError(errorMessage));
      console.error('Dashboard load error:', err);
    } finally {
      dispatch(setLoading(false));
    }
  }, [dispatch]);

  // Pull-to-refresh
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await loadDashboardData();
    } finally {
      setRefreshing(false);
    }
  }, [loadDashboardData]);

  // Load notifications
  const loadNotifications = useCallback(async () => {
    try {
      const unreadNotifications = await NotificationService.getUnreadNotifications();
      setNotifications(unreadNotifications.slice(0, 3)); // Show top 3
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  }, []);

  // Focus effect - reload when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      loadDashboardData();
      loadNotifications();
    }, [loadDashboardData, loadNotifications])
  );

  // Quick actions handler
  const handleQuickAction = useCallback((actionId: string) => {
    switch (actionId) {
      case 'add_lead':
        // Navigate to add lead screen
        console.log('Navigate to add lead');
        break;
      case 'scan_card':
        // Navigate to camera for business card scanning
        console.log('Navigate to card scanner');
        break;
      case 'voice_note':
        // Navigate to voice note recording
        console.log('Navigate to voice note');
        break;
      case 'schedule_tour':
        // Navigate to tour scheduling
        console.log('Navigate to tour scheduler');
        break;
      default:
        Alert.alert('Feature Coming Soon', `${actionId} will be available soon!`);
    }
  }, []);

  if (isLoading && !dashboardData) {
    return (
      <View style={styles.container}>
        <Header
          title={`Welcome back, ${user?.firstName || 'User'}`}
          showNotificationBadge={notifications.length > 0}
        />
        <LoadingSpinner size="large" message="Loading your dashboard..." />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Header
          title={`Welcome back, ${user?.firstName || 'User'}`}
          showNotificationBadge={false}
        />
        <ErrorMessage
          message={error}
          onRetry={loadDashboardData}
          retryButtonText="Reload Dashboard"
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Header
        title={`Welcome back, ${user?.firstName || 'User'}`}
        showNotificationBadge={notifications.length > 0}
        onNotificationPress={() => console.log('Navigate to notifications')}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[theme.colors.primary]}
            tintColor={theme.colors.primary}
          />
        }>

        {/* Notification Banner */}
        {notifications.length > 0 && (
          <NotificationBanner
            notifications={notifications}
            onDismiss={() => setNotifications([])}
            onViewAll={() => console.log('Navigate to notifications')}
          />
        )}

        {/* Key Metrics */}
        {dashboardData && (
          <View style={styles.metricsContainer}>
            <View style={styles.metricsRow}>
              <MetricCard
                title="Total Leads"
                value={dashboardData.leads_summary.total_count.toString()}
                change={`+${dashboardData.leads_summary.new_today} today`}
                changeType="positive"
                icon="people"
                style={styles.metricCard}
              />
              <MetricCard
                title="Hot Leads"
                value={dashboardData.leads_summary.hot_leads.toString()}
                change="Ready to close"
                changeType="positive"
                icon="whatshot"
                style={styles.metricCard}
              />
            </View>
            <View style={styles.metricsRow}>
              <MetricCard
                title="Conversion Rate"
                value={`${(dashboardData.performance_metrics.conversion_rate * 100).toFixed(1)}%`}
                change="This week"
                changeType="neutral"
                icon="trending-up"
                style={styles.metricCard}
              />
              <MetricCard
                title="Avg Response"
                value={`${dashboardData.performance_metrics.avg_response_time}min`}
                change="Response time"
                changeType="positive"
                icon="schedule"
                style={styles.metricCard}
              />
            </View>
          </View>
        )}

        {/* Quick Actions */}
        {dashboardData && (
          <QuickActionGrid
            actions={dashboardData.quick_actions}
            onActionPress={handleQuickAction}
            style={styles.quickActions}
          />
        )}

        {/* Recent Activity */}
        <RecentActivity
          style={styles.recentActivity}
        />

      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: theme.spacing.md,
  },
  metricsContainer: {
    marginBottom: theme.spacing.lg,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.md,
  },
  metricCard: {
    width: (width - theme.spacing.md * 3) / 2,
  },
  quickActions: {
    marginBottom: theme.spacing.lg,
  },
  recentActivity: {
    marginBottom: theme.spacing.xl,
  },
});