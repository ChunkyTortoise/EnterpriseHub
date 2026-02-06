/**
 * Mobile Billing Service - In-App Purchases and Subscriptions
 * Handles iOS and Android billing with Stripe integration
 */

import React from 'react';
import {Platform, Alert} from 'react-native';
import RNIap, {
  initConnection,
  endConnection,
  purchaseErrorListener,
  purchaseUpdatedListener,
  getProducts,
  requestPurchase,
  requestSubscription,
  finishTransaction,
  getPurchaseHistory,
  getAvailablePurchases,
  validateReceiptIos,
  validateReceiptAndroid,
} from 'react-native-iap';

import {ApiService} from './ApiService';
import {AnalyticsService} from './AnalyticsService';

// Product IDs for in-app purchases
const PREMIUM_PRODUCTS = {
  ios: [
    'com.ghl.realestate.premium_monthly',
    'com.ghl.realestate.premium_annual',
    'com.ghl.realestate.advanced_analytics',
    'com.ghl.realestate.unlimited_leads',
    'com.ghl.realestate.ar_visualization',
    'com.ghl.realestate.priority_support',
  ],
  android: [
    'premium_monthly',
    'premium_annual',
    'advanced_analytics',
    'unlimited_leads',
    'ar_visualization',
    'priority_support',
  ],
};

// Subscription IDs
const SUBSCRIPTION_PRODUCTS = {
  ios: [
    'com.ghl.realestate.premium_subscription',
    'com.ghl.realestate.enterprise_subscription',
  ],
  android: [
    'premium_subscription',
    'enterprise_subscription',
  ],
};

// Feature pricing tiers
const PRICING_TIERS = {
  premium_monthly: {
    price: '$49.99',
    features: ['Advanced Analytics', 'Priority Lead Notifications', '500 Lead Limit'],
    tier: 'premium',
  },
  premium_annual: {
    price: '$499.99',
    features: ['Advanced Analytics', 'Priority Lead Notifications', 'Unlimited Leads', 'AR Visualization'],
    tier: 'premium',
    savings: '17% off monthly',
  },
  advanced_analytics: {
    price: '$19.99',
    features: ['Advanced Reporting', 'Predictive Analytics', 'Custom Dashboards'],
    tier: 'addon',
  },
  unlimited_leads: {
    price: '$29.99',
    features: ['Unlimited Lead Management', 'Bulk Operations', 'Lead Export'],
    tier: 'addon',
  },
  ar_visualization: {
    price: '$39.99',
    features: ['AR Property Visualization', '3D Property Tours', 'Virtual Staging'],
    tier: 'addon',
  },
  priority_support: {
    price: '$14.99',
    features: ['24/7 Priority Support', 'Phone Support', 'Dedicated Account Manager'],
    tier: 'addon',
  },
};

class MobileBillingService {
  constructor() {
    this.purchaseUpdateSubscription = null;
    this.purchaseErrorSubscription = null;
    this.isInitialized = false;
    this.availableProducts = [];
    this.availableSubscriptions = [];
    this.currentPurchases = [];
  }

  async initialize() {
    if (this.isInitialized) return;

    try {
      // Initialize IAP connection
      await initConnection();
      console.log('📱 In-app purchases initialized');

      // Set up listeners
      this.setupPurchaseListeners();

      // Load available products
      await this.loadProducts();

      // Restore previous purchases
      await this.restorePurchases();

      this.isInitialized = true;

    } catch (error) {
      console.error('❌ Failed to initialize billing service:', error);
      throw error;
    }
  }

  setupPurchaseListeners() {
    // Purchase update listener
    this.purchaseUpdateSubscription = purchaseUpdatedListener(async (purchase) => {
      console.log('📦 Purchase updated:', purchase);

      try {
        await this.processPurchase(purchase);
      } catch (error) {
        console.error('❌ Failed to process purchase:', error);
        Alert.alert(
          'Purchase Error',
          'There was a problem processing your purchase. Please contact support if this persists.'
        );
      }
    });

    // Purchase error listener
    this.purchaseErrorSubscription = purchaseErrorListener((error) => {
      console.error('❌ Purchase error:', error);

      // Handle different error types
      if (error.code === 'E_USER_CANCELLED') {
        // User cancelled - no need to show error
        return;
      }

      Alert.alert(
        'Purchase Failed',
        error.message || 'Unable to complete purchase. Please try again.'
      );
    });
  }

  async loadProducts() {
    try {
      const platform = Platform.OS;

      // Load one-time purchases
      const products = await getProducts(PREMIUM_PRODUCTS[platform]);
      this.availableProducts = products;

      // Load subscriptions
      const subscriptions = await getProducts(SUBSCRIPTION_PRODUCTS[platform]);
      this.availableSubscriptions = subscriptions;

      console.log(`📦 Loaded ${products.length} products and ${subscriptions.length} subscriptions`);

    } catch (error) {
      console.error('❌ Failed to load products:', error);
    }
  }

  async restorePurchases() {
    try {
      const purchases = await getAvailablePurchases();
      this.currentPurchases = purchases;

      // Validate and sync with server
      for (const purchase of purchases) {
        await this.validatePurchase(purchase);
      }

      console.log(`🔄 Restored ${purchases.length} purchases`);

    } catch (error) {
      console.error('❌ Failed to restore purchases:', error);
    }
  }

  async purchaseProduct(productId) {
    try {
      if (!this.isInitialized) {
        throw new Error('Billing service not initialized');
      }

      console.log(`💳 Purchasing product: ${productId}`);

      // Track purchase attempt
      AnalyticsService.track('purchase_attempt', {
        product_id: productId,
        platform: Platform.OS,
      });

      // Request purchase
      await requestPurchase(productId);

    } catch (error) {
      console.error('❌ Purchase request failed:', error);

      // Track failed purchase
      AnalyticsService.track('purchase_failed', {
        product_id: productId,
        error: error.message,
      });

      throw error;
    }
  }

  async subscribeToProduct(subscriptionId) {
    try {
      if (!this.isInitialized) {
        throw new Error('Billing service not initialized');
      }

      console.log(`🔄 Subscribing to: ${subscriptionId}`);

      // Track subscription attempt
      AnalyticsService.track('subscription_attempt', {
        subscription_id: subscriptionId,
        platform: Platform.OS,
      });

      // Request subscription
      await requestSubscription(subscriptionId);

    } catch (error) {
      console.error('❌ Subscription request failed:', error);

      // Track failed subscription
      AnalyticsService.track('subscription_failed', {
        subscription_id: subscriptionId,
        error: error.message,
      });

      throw error;
    }
  }

  async processPurchase(purchase) {
    try {
      // Validate receipt with Apple/Google
      let validationResult;

      if (Platform.OS === 'ios') {
        validationResult = await validateReceiptIos({
          'receipt-data': purchase.transactionReceipt,
          password: 'your_shared_secret', // App Store Connect shared secret
        });
      } else {
        validationResult = await validateReceiptAndroid({
          packageName: 'com.ghl.realestate',
          productId: purchase.productId,
          purchaseToken: purchase.purchaseToken,
          accessToken: 'your_google_play_access_token',
        });
      }

      // Validate with backend
      const serverValidation = await ApiService.validatePurchase({
        platform: Platform.OS,
        productId: purchase.productId,
        transactionId: purchase.transactionId,
        receipt: purchase.transactionReceipt,
        validationResult: validationResult,
      });

      if (serverValidation.valid) {
        // Unlock features
        await this.unlockFeatures(purchase.productId);

        // Track successful purchase
        AnalyticsService.track('purchase_completed', {
          product_id: purchase.productId,
          transaction_id: purchase.transactionId,
          revenue: this.getProductPrice(purchase.productId),
        });

        // Show success message
        Alert.alert(
          'Purchase Successful!',
          'Your new features have been unlocked and are ready to use.',
          [{text: 'OK', style: 'default'}]
        );

        // Finish transaction
        await finishTransaction(purchase);

      } else {
        throw new Error('Purchase validation failed');
      }

    } catch (error) {
      console.error('❌ Failed to process purchase:', error);
      throw error;
    }
  }

  async unlockFeatures(productId) {
    try {
      // Update local feature flags
      const features = this.getProductFeatures(productId);

      // Send to backend to update user subscription
      await ApiService.updateUserSubscription({
        productId: productId,
        features: features,
        platform: Platform.OS,
      });

      console.log(`🔓 Unlocked features for product: ${productId}`);

    } catch (error) {
      console.error('❌ Failed to unlock features:', error);
    }
  }

  async validatePurchase(purchase) {
    try {
      const validation = await ApiService.validatePurchase({
        platform: Platform.OS,
        productId: purchase.productId,
        transactionId: purchase.transactionId,
        receipt: purchase.transactionReceipt,
      });

      if (validation.valid) {
        await this.unlockFeatures(purchase.productId);
      }

      return validation;

    } catch (error) {
      console.error('❌ Purchase validation failed:', error);
      return { valid: false, error: error.message };
    }
  }

  getAvailableProducts() {
    return this.availableProducts.map(product => ({
      ...product,
      pricing: PRICING_TIERS[product.productId],
      features: this.getProductFeatures(product.productId),
    }));
  }

  getAvailableSubscriptions() {
    return this.availableSubscriptions.map(subscription => ({
      ...subscription,
      pricing: PRICING_TIERS[subscription.productId],
      features: this.getProductFeatures(subscription.productId),
    }));
  }

  getProductFeatures(productId) {
    const pricing = PRICING_TIERS[productId];
    return pricing ? pricing.features : [];
  }

  getProductPrice(productId) {
    const product = this.availableProducts.find(p => p.productId === productId) ||
                   this.availableSubscriptions.find(s => s.productId === productId);

    return product ? parseFloat(product.price) : 0;
  }

  isPremiumUser() {
    return this.currentPurchases.some(purchase =>
      purchase.productId.includes('premium') ||
      purchase.productId.includes('enterprise')
    );
  }

  hasFeature(feature) {
    // Check if user has purchased a product that includes this feature
    for (const purchase of this.currentPurchases) {
      const features = this.getProductFeatures(purchase.productId);
      if (features.some(f => f.toLowerCase().includes(feature.toLowerCase()))) {
        return true;
      }
    }
    return false;
  }

  async getSubscriptionStatus() {
    try {
      const status = await ApiService.getSubscriptionStatus();
      return {
        isActive: status.active,
        tier: status.tier,
        expiresAt: status.expiresAt,
        features: status.features,
        nextBillingDate: status.nextBillingDate,
      };
    } catch (error) {
      console.error('❌ Failed to get subscription status:', error);
      return {
        isActive: false,
        tier: 'free',
        features: [],
      };
    }
  }

  async cancelSubscription(subscriptionId) {
    try {
      // Note: Actual cancellation happens through App Store/Play Store
      // This just notifies our backend
      await ApiService.cancelSubscription({
        subscriptionId: subscriptionId,
        platform: Platform.OS,
      });

      Alert.alert(
        'Subscription Cancelled',
        'Your subscription has been cancelled. You will continue to have access until the end of your billing period.',
        [{text: 'OK', style: 'default'}]
      );

    } catch (error) {
      console.error('❌ Failed to cancel subscription:', error);
      throw error;
    }
  }

  async showPaywall(context = 'general') {
    try {
      // Track paywall view
      AnalyticsService.track('paywall_viewed', {
        context: context,
        products_shown: this.availableProducts.length,
      });

      // Show paywall UI (this would be implemented in React components)
      console.log(`💰 Showing paywall for context: ${context}`);

    } catch (error) {
      console.error('❌ Failed to show paywall:', error);
    }
  }

  async applyPromoCode(promoCode) {
    try {
      const result = await ApiService.applyPromoCode({
        code: promoCode,
        platform: Platform.OS,
      });

      if (result.valid) {
        Alert.alert(
          'Promo Code Applied!',
          `You've received: ${result.benefit}`,
          [{text: 'OK', style: 'default'}]
        );

        // Track promo code usage
        AnalyticsService.track('promo_code_applied', {
          code: promoCode,
          benefit: result.benefit,
        });

        return result;
      } else {
        Alert.alert(
          'Invalid Promo Code',
          'The promo code you entered is not valid or has expired.'
        );
        return { valid: false };
      }

    } catch (error) {
      console.error('❌ Failed to apply promo code:', error);
      throw error;
    }
  }

  async trackRevenue(productId, revenue) {
    try {
      // Track with analytics service
      AnalyticsService.track('revenue', {
        product_id: productId,
        revenue: revenue,
        currency: 'USD',
        platform: Platform.OS,
      });

      // Send to backend for revenue tracking
      await ApiService.trackMobileRevenue({
        productId: productId,
        revenue: revenue,
        platform: Platform.OS,
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      console.error('❌ Failed to track revenue:', error);
    }
  }

  destroy() {
    // Remove listeners
    if (this.purchaseUpdateSubscription) {
      this.purchaseUpdateSubscription.remove();
      this.purchaseUpdateSubscription = null;
    }

    if (this.purchaseErrorSubscription) {
      this.purchaseErrorSubscription.remove();
      this.purchaseErrorSubscription = null;
    }

    // End IAP connection
    endConnection().catch(console.error);

    console.log('💳 Billing service destroyed');
  }
}

export default new MobileBillingService();