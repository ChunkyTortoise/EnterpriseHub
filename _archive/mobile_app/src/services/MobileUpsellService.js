/**
 * Mobile Upselling Service - Context-Aware Feature Promotion
 * Intelligent upselling based on user behavior and app usage patterns
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import {Alert} from 'react-native';

import {AnalyticsService} from './AnalyticsService';
import MobileBillingService from './MobileBillingService';
import {ApiService} from './ApiService';

// Upselling triggers and contexts
const UPSELL_TRIGGERS = {
  LEAD_LIMIT_REACHED: 'lead_limit_reached',
  ANALYTICS_VIEW: 'analytics_view',
  AR_FEATURE_ATTEMPT: 'ar_feature_attempt',
  VOICE_NOTE_ATTEMPT: 'voice_note_attempt',
  BULK_OPERATION: 'bulk_operation',
  PROPERTY_SEARCH_LIMIT: 'property_search_limit',
  EXPORT_ATTEMPT: 'export_attempt',
  SUPPORT_NEEDED: 'support_needed',
  PERFORMANCE_ISSUE: 'performance_issue',
  FEATURE_DISCOVERY: 'feature_discovery',
};

// Upselling strategies
const UPSELLING_STRATEGIES = {
  IMMEDIATE_BLOCK: 'immediate_block',        // Block feature, show paywall immediately
  SOFT_PROMPT: 'soft_prompt',               // Show gentle promotion
  TRIAL_OFFER: 'trial_offer',               // Offer free trial
  USAGE_BASED: 'usage_based',               // Show after multiple uses
  TIME_DELAYED: 'time_delayed',             // Show after time delay
  CONTEXTUAL_HINT: 'contextual_hint',       // Subtle hint in UI
};

// Feature upgrade mappings
const FEATURE_UPGRADES = {
  [UPSELL_TRIGGERS.LEAD_LIMIT_REACHED]: {
    product: 'unlimited_leads',
    strategy: UPSELLING_STRATEGIES.IMMEDIATE_BLOCK,
    title: 'Upgrade to Unlimited Leads',
    message: 'You\'ve reached your lead limit. Upgrade to manage unlimited leads and grow your business.',
    benefits: ['Unlimited lead management', 'Bulk operations', 'Lead export', 'Priority sync'],
    urgency: 'high',
  },
  [UPSELL_TRIGGERS.ANALYTICS_VIEW]: {
    product: 'advanced_analytics',
    strategy: UPSELLING_STRATEGIES.SOFT_PROMPT,
    title: 'Unlock Advanced Analytics',
    message: 'Get deeper insights with advanced analytics and predictive reporting.',
    benefits: ['Conversion tracking', 'Revenue forecasting', 'Custom dashboards', 'Automated reports'],
    urgency: 'medium',
  },
  [UPSELL_TRIGGERS.AR_FEATURE_ATTEMPT]: {
    product: 'ar_visualization',
    strategy: UPSELLING_STRATEGIES.TRIAL_OFFER,
    title: 'Experience AR Visualization',
    message: 'Transform how your clients view properties with AR technology.',
    benefits: ['3D property tours', 'Virtual staging', 'Interactive walkthroughs', 'Client engagement'],
    urgency: 'high',
    trial_days: 7,
  },
  [UPSELL_TRIGGERS.VOICE_NOTE_ATTEMPT]: {
    product: 'premium_monthly',
    strategy: UPSELLING_STRATEGIES.CONTEXTUAL_HINT,
    title: 'Upgrade for Voice Features',
    message: 'Save time with voice-to-text notes and AI transcription.',
    benefits: ['Voice notes', 'AI transcription', 'Hands-free operation', 'Faster lead updates'],
    urgency: 'low',
  },
  [UPSELL_TRIGGERS.SUPPORT_NEEDED]: {
    product: 'priority_support',
    strategy: UPSELLING_STRATEGIES.IMMEDIATE_BLOCK,
    title: 'Get Priority Support',
    message: 'Need help? Upgrade to priority support for immediate assistance.',
    benefits: ['24/7 phone support', 'Dedicated account manager', 'Priority response', 'Setup assistance'],
    urgency: 'high',
  },
};

class MobileUpsellService {
  constructor() {
    this.upsellHistory = new Map();
    this.userBehavior = new Map();
    this.cooldownPeriods = new Map();
    this.isInitialized = false;
  }

  async initialize() {
    if (this.isInitialized) return;

    try {
      // Load upsell history from storage
      await this.loadUpsellHistory();

      // Load user behavior data
      await this.loadUserBehavior();

      this.isInitialized = true;
      console.log('🎯 Mobile upsell service initialized');

    } catch (error) {
      console.error('❌ Failed to initialize upsell service:', error);
    }
  }

  async triggerUpsell(trigger, context = {}) {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      // Check if user is already premium
      if (MobileBillingService.isPremiumUser()) {
        console.log('👑 User is premium, skipping upsell');
        return null;
      }

      // Get upselling configuration for trigger
      const upsellConfig = FEATURE_UPGRADES[trigger];
      if (!upsellConfig) {
        console.log(`⚠️ No upsell config for trigger: ${trigger}`);
        return null;
      }

      // Check cooldown period
      if (this.isInCooldown(trigger)) {
        console.log(`⏰ Upsell trigger ${trigger} is in cooldown`);
        return null;
      }

      // Analyze user behavior and determine best strategy
      const strategy = await this.determineOptimalStrategy(trigger, context);

      // Track upsell opportunity
      await this.trackUpsellOpportunity(trigger, strategy, context);

      // Execute upselling strategy
      const result = await this.executeUpsellStrategy(upsellConfig, strategy, context);

      // Update upsell history
      await this.updateUpsellHistory(trigger, result);

      return result;

    } catch (error) {
      console.error('❌ Upsell trigger failed:', error);
      return null;
    }
  }

  async determineOptimalStrategy(trigger, context) {
    try {
      // Get user behavior data
      const behavior = this.userBehavior.get('user') || {};

      // Get base strategy from configuration
      const baseStrategy = FEATURE_UPGRADES[trigger]?.strategy || UPSELLING_STRATEGIES.SOFT_PROMPT;

      // Adjust strategy based on user behavior
      const appUsage = behavior.appUsage || {};
      const upsellHistory = this.upsellHistory.get(trigger) || [];

      // If user has dismissed this upsell multiple times, use softer approach
      if (upsellHistory.filter(h => h.action === 'dismissed').length >= 3) {
        return UPSELLING_STRATEGIES.CONTEXTUAL_HINT;
      }

      // If user is highly engaged, use trial offers
      if (appUsage.sessionCount > 50 && appUsage.avgSessionDuration > 10) {
        return UPSELLING_STRATEGIES.TRIAL_OFFER;
      }

      // If user is new, use soft prompts
      if (appUsage.sessionCount < 10) {
        return UPSELLING_STRATEGIES.SOFT_PROMPT;
      }

      // For power users hitting limits, use immediate blocking
      if (trigger === UPSELL_TRIGGERS.LEAD_LIMIT_REACHED ||
          trigger === UPSELL_TRIGGERS.PROPERTY_SEARCH_LIMIT) {
        return UPSELLING_STRATEGIES.IMMEDIATE_BLOCK;
      }

      return baseStrategy;

    } catch (error) {
      console.error('❌ Failed to determine optimal strategy:', error);
      return UPSELLING_STRATEGIES.SOFT_PROMPT;
    }
  }

  async executeUpsellStrategy(upsellConfig, strategy, context) {
    try {
      switch (strategy) {
        case UPSELLING_STRATEGIES.IMMEDIATE_BLOCK:
          return await this.showBlockingPaywall(upsellConfig, context);

        case UPSELLING_STRATEGIES.SOFT_PROMPT:
          return await this.showSoftPrompt(upsellConfig, context);

        case UPSELLING_STRATEGIES.TRIAL_OFFER:
          return await this.showTrialOffer(upsellConfig, context);

        case UPSELLING_STRATEGIES.USAGE_BASED:
          return await this.showUsageBasedPrompt(upsellConfig, context);

        case UPSELLING_STRATEGIES.CONTEXTUAL_HINT:
          return await this.showContextualHint(upsellConfig, context);

        default:
          return await this.showSoftPrompt(upsellConfig, context);
      }

    } catch (error) {
      console.error('❌ Failed to execute upsell strategy:', error);
      return { success: false, action: 'error', error: error.message };
    }
  }

  async showBlockingPaywall(upsellConfig, context) {
    return new Promise((resolve) => {
      Alert.alert(
        upsellConfig.title,
        upsellConfig.message,
        [
          {
            text: 'Maybe Later',
            style: 'cancel',
            onPress: () => {
              this.setCooldown(upsellConfig.product, 24); // 24 hour cooldown
              resolve({ success: false, action: 'dismissed' });
            }
          },
          {
            text: `Upgrade ${upsellConfig.urgency === 'high' ? 'Now' : ''}`,
            style: 'default',
            onPress: async () => {
              try {
                await MobileBillingService.purchaseProduct(upsellConfig.product);
                resolve({ success: true, action: 'purchased', product: upsellConfig.product });
              } catch (error) {
                resolve({ success: false, action: 'purchase_failed', error: error.message });
              }
            }
          }
        ],
        { cancelable: false }
      );
    });
  }

  async showSoftPrompt(upsellConfig, context) {
    return new Promise((resolve) => {
      Alert.alert(
        upsellConfig.title,
        `${upsellConfig.message}\n\nBenefits:\n${upsellConfig.benefits.map(b => `• ${b}`).join('\n')}`,
        [
          {
            text: 'Not Now',
            style: 'cancel',
            onPress: () => {
              this.setCooldown(upsellConfig.product, 12); // 12 hour cooldown
              resolve({ success: false, action: 'dismissed' });
            }
          },
          {
            text: 'Learn More',
            style: 'default',
            onPress: () => {
              // Show detailed feature comparison
              resolve({ success: false, action: 'learn_more' });
            }
          },
          {
            text: 'Upgrade',
            style: 'default',
            onPress: async () => {
              try {
                await MobileBillingService.purchaseProduct(upsellConfig.product);
                resolve({ success: true, action: 'purchased', product: upsellConfig.product });
              } catch (error) {
                resolve({ success: false, action: 'purchase_failed', error: error.message });
              }
            }
          }
        ]
      );
    });
  }

  async showTrialOffer(upsellConfig, context) {
    const trialDays = upsellConfig.trial_days || 7;

    return new Promise((resolve) => {
      Alert.alert(
        `Try ${upsellConfig.title} Free!`,
        `${upsellConfig.message}\n\nStart your ${trialDays}-day free trial now. Cancel anytime.`,
        [
          {
            text: 'Not Interested',
            style: 'cancel',
            onPress: () => {
              this.setCooldown(upsellConfig.product, 48); // 48 hour cooldown
              resolve({ success: false, action: 'dismissed' });
            }
          },
          {
            text: `Start ${trialDays}-Day Trial`,
            style: 'default',
            onPress: async () => {
              try {
                await this.startFreeTrial(upsellConfig.product, trialDays);
                resolve({ success: true, action: 'trial_started', product: upsellConfig.product });
              } catch (error) {
                resolve({ success: false, action: 'trial_failed', error: error.message });
              }
            }
          }
        ]
      );
    });
  }

  async showUsageBasedPrompt(upsellConfig, context) {
    // Show prompt only after user has attempted the feature multiple times
    const attemptCount = await this.getFeatureAttemptCount(upsellConfig.product);

    if (attemptCount < 3) {
      // Increment attempt count and show hint
      await this.incrementFeatureAttemptCount(upsellConfig.product);
      return { success: false, action: 'hint_shown' };
    }

    return await this.showSoftPrompt(upsellConfig, context);
  }

  async showContextualHint(upsellConfig, context) {
    // This would typically show a subtle UI element rather than a blocking alert
    // For now, we'll just track the hint
    console.log(`💡 Showing contextual hint for ${upsellConfig.product}`);

    return { success: false, action: 'hint_shown', product: upsellConfig.product };
  }

  async startFreeTrial(productId, days) {
    try {
      // Call backend to start free trial
      const trial = await ApiService.startFreeTrial({
        productId: productId,
        trialDays: days,
        platform: 'mobile',
      });

      // Track trial start
      AnalyticsService.track('trial_started', {
        product_id: productId,
        trial_days: days,
      });

      return trial;

    } catch (error) {
      console.error('❌ Failed to start free trial:', error);
      throw error;
    }
  }

  async trackUpsellOpportunity(trigger, strategy, context) {
    try {
      const event = {
        trigger: trigger,
        strategy: strategy,
        context: context,
        timestamp: new Date().toISOString(),
      };

      // Track with analytics
      AnalyticsService.track('upsell_opportunity', event);

      // Send to backend for analysis
      await ApiService.trackUpsellEvent(event);

    } catch (error) {
      console.error('❌ Failed to track upsell opportunity:', error);
    }
  }

  async updateUpsellHistory(trigger, result) {
    try {
      const history = this.upsellHistory.get(trigger) || [];

      history.push({
        ...result,
        timestamp: new Date().toISOString(),
      });

      // Keep only last 10 entries per trigger
      if (history.length > 10) {
        history.splice(0, history.length - 10);
      }

      this.upsellHistory.set(trigger, history);

      // Save to storage
      await this.saveUpsellHistory();

    } catch (error) {
      console.error('❌ Failed to update upsell history:', error);
    }
  }

  isInCooldown(trigger) {
    const cooldownKey = `cooldown_${trigger}`;
    const cooldownEnd = this.cooldownPeriods.get(cooldownKey);

    if (!cooldownEnd) return false;

    return new Date() < new Date(cooldownEnd);
  }

  setCooldown(trigger, hours) {
    const cooldownKey = `cooldown_${trigger}`;
    const cooldownEnd = new Date(Date.now() + hours * 60 * 60 * 1000);

    this.cooldownPeriods.set(cooldownKey, cooldownEnd.toISOString());
    this.saveCooldownPeriods();
  }

  async getFeatureAttemptCount(productId) {
    try {
      const key = `feature_attempts_${productId}`;
      const count = await AsyncStorage.getItem(key);
      return parseInt(count) || 0;
    } catch (error) {
      return 0;
    }
  }

  async incrementFeatureAttemptCount(productId) {
    try {
      const key = `feature_attempts_${productId}`;
      const currentCount = await this.getFeatureAttemptCount(productId);
      await AsyncStorage.setItem(key, (currentCount + 1).toString());
    } catch (error) {
      console.error('Failed to increment feature attempt count:', error);
    }
  }

  async loadUpsellHistory() {
    try {
      const stored = await AsyncStorage.getItem('upsell_history');
      if (stored) {
        const parsed = JSON.parse(stored);
        this.upsellHistory = new Map(Object.entries(parsed));
      }
    } catch (error) {
      console.error('Failed to load upsell history:', error);
    }
  }

  async saveUpsellHistory() {
    try {
      const obj = Object.fromEntries(this.upsellHistory);
      await AsyncStorage.setItem('upsell_history', JSON.stringify(obj));
    } catch (error) {
      console.error('Failed to save upsell history:', error);
    }
  }

  async loadUserBehavior() {
    try {
      const stored = await AsyncStorage.getItem('user_behavior');
      if (stored) {
        const parsed = JSON.parse(stored);
        this.userBehavior = new Map(Object.entries(parsed));
      }
    } catch (error) {
      console.error('Failed to load user behavior:', error);
    }
  }

  async saveCooldownPeriods() {
    try {
      const obj = Object.fromEntries(this.cooldownPeriods);
      await AsyncStorage.setItem('cooldown_periods', JSON.stringify(obj));
    } catch (error) {
      console.error('Failed to save cooldown periods:', error);
    }
  }

  // Public API for triggering specific upsells
  async triggerLeadLimitUpsell(currentCount, limit) {
    return await this.triggerUpsell(UPSELL_TRIGGERS.LEAD_LIMIT_REACHED, {
      currentCount,
      limit,
    });
  }

  async triggerAnalyticsUpsell() {
    return await this.triggerUpsell(UPSELL_TRIGGERS.ANALYTICS_VIEW);
  }

  async triggerARUpsell() {
    return await this.triggerUpsell(UPSELL_TRIGGERS.AR_FEATURE_ATTEMPT);
  }

  async triggerVoiceNoteUpsell() {
    return await this.triggerUpsell(UPSELL_TRIGGERS.VOICE_NOTE_ATTEMPT);
  }

  async triggerSupportUpsell() {
    return await this.triggerUpsell(UPSELL_TRIGGERS.SUPPORT_NEEDED);
  }

  // Analytics and reporting
  async getUpsellMetrics() {
    try {
      const metrics = await ApiService.getUpsellMetrics();
      return {
        conversionRate: metrics.conversionRate,
        revenueFromUpsells: metrics.revenueFromUpsells,
        topPerformingTriggers: metrics.topPerformingTriggers,
        averageTimeToConversion: metrics.averageTimeToConversion,
      };
    } catch (error) {
      console.error('Failed to get upsell metrics:', error);
      return null;
    }
  }
}

export default new MobileUpsellService();