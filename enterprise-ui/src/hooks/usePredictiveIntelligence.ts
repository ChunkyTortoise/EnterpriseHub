/**
 * Predictive Intelligence Hook for Jorge's Crystal Ball Technology
 * Provides real-time predictive insights and forecasting capabilities
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Types for predictive intelligence
interface PredictionRequest {
  type: 'market_movement' | 'client_behavior' | 'deal_outcome' | 'business_metrics';
  parameters: Record<string, any>;
  context?: Record<string, any>;
}

interface PredictionResult {
  prediction_id: string;
  type: string;
  result: Record<string, any>;
  confidence: number;
  explanation: string;
  supporting_factors: string[];
  risk_factors: string[];
  actionable_insights: string[];
  jorge_methodology_application: string;
  created_at: string;
  expires_at?: string;
}

interface MarketMovementPrediction {
  location_id: string;
  current_median_price: number;
  predicted_price_30_days: number;
  predicted_price_90_days: number;
  price_change_percentage: number;
  market_velocity: 'accelerating' | 'steady' | 'slowing';
  inventory_trend: 'increasing' | 'stable' | 'decreasing';
  demand_forecast: 'high' | 'moderate' | 'low';
  optimal_listing_window: { start: string; end: string };
  optimal_buying_window: { start: string; end: string };
  jorge_advantage_score: number;
}

interface ClientBehaviorPrediction {
  client_id: string;
  purchase_probability: number;
  predicted_timeframe: 'immediate' | 'short_term' | 'medium_term' | 'long_term';
  predicted_budget_range: { min: number; max: number; target: number };
  negotiation_style: 'aggressive' | 'collaborative' | 'analytical' | 'emotional';
  decision_factors: string[];
  optimal_approach_timing: string;
  referral_potential: number;
  lifetime_value_prediction: number;
  churn_risk: number;
  jorge_methodology_fit: number;
}

interface DealOutcomePrediction {
  deal_id: string;
  closing_probability: number;
  predicted_closing_date: string;
  predicted_final_price: number;
  commission_probability_6_percent: number;
  risk_factors: Array<{ type: string; severity: string; description: string }>;
  success_accelerators: string[];
  recommended_actions: Array<{ action: string; timing: string; priority: string }>;
  negotiation_leverage: 'strong' | 'moderate' | 'weak';
  timeline_accuracy: number;
}

interface BusinessForecast {
  timeframe: string;
  revenue_forecast: {
    base: number;
    optimistic: number;
    conservative: number;
    confidence: number;
  };
  market_share_projection: {
    current: number;
    projected: Record<string, number>;
    growth_trajectory: string;
  };
  team_performance: {
    current_size: number;
    projected_size: Record<string, number>;
    productivity_optimization: number;
  };
  business_opportunities: Array<{
    type: string;
    market_size: number;
    roi_projection: number;
    success_probability: number;
  }>;
}

interface PredictionCache {
  [key: string]: {
    data: any;
    timestamp: number;
    expires_at: number;
  };
}

const usePredictiveIntelligence = () => {
  const [predictions, setPredictions] = useState<Record<string, PredictionResult>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [cache, setCache] = useState<PredictionCache>({});
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();

  // Voice commands for mobile prediction requests
  const voiceCommands = [
    {
      patterns: ['predict market', 'market prediction', 'what will market do'],
      action: 'PREDICT_MARKET_MOVEMENT',
      description: 'Get market movement predictions'
    },
    {
      patterns: ['predict client', 'client behavior', 'when will client buy'],
      action: 'PREDICT_CLIENT_BEHAVIOR',
      description: 'Analyze client behavior and timing'
    },
    {
      patterns: ['deal outcome', 'will deal close', 'closing probability'],
      action: 'PREDICT_DEAL_OUTCOME',
      description: 'Predict deal success probability'
    },
    {
      patterns: ['business forecast', 'revenue prediction', 'how much will I make'],
      action: 'PREDICT_BUSINESS_METRICS',
      description: 'Generate business forecasts'
    }
  ];

  // Initialize WebSocket connection for real-time predictions
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/prediction-updates`);

        ws.onopen = () => {
          console.log('Connected to prediction intelligence WebSocket');
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            switch (data.type) {
              case 'prediction_update':
                handlePredictionUpdate(data.prediction);
                break;
              case 'market_alert':
                handleMarketAlert(data.alert);
                break;
              case 'opportunity_alert':
                handleOpportunityAlert(data.opportunity);
                break;
              case 'risk_alert':
                handleRiskAlert(data.risk);
                break;
            }
          } catch (error) {
            console.error('Error parsing prediction message:', error);
          }
        };

        ws.onclose = () => {
          console.log('Disconnected from prediction intelligence WebSocket');
          setIsConnected(false);

          // Reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = (error) => {
          console.error('Prediction WebSocket error:', error);
        };

        wsRef.current = ws;
      } catch (error) {
        console.error('Failed to connect to prediction WebSocket:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Cache management
  const getCachedPrediction = useCallback((key: string) => {
    const cached = cache[key];
    if (cached && Date.now() < cached.expires_at) {
      return cached.data;
    }
    return null;
  }, [cache]);

  const setCachedPrediction = useCallback((key: string, data: any, expiresIn: number = 300000) => {
    setCache(prev => ({
      ...prev,
      [key]: {
        data,
        timestamp: Date.now(),
        expires_at: Date.now() + expiresIn
      }
    }));
  }, []);

  // Predict market movement
  const predictMarketMovement = useCallback(async (
    location: { lat: number; lng: number },
    timeframe: 'short_term' | 'medium_term' | 'long_term' = 'medium_term'
  ): Promise<MarketMovementPrediction> => {
    const cacheKey = `market_${location.lat}_${location.lng}_${timeframe}`;
    const cached = getCachedPrediction(cacheKey);
    if (cached) return cached;

    const response = await fetch('/api/prediction/market-movement', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location, timeframe })
    });

    if (!response.ok) {
      throw new Error('Failed to predict market movement');
    }

    const data = await response.json();
    setCachedPrediction(cacheKey, data, 1800000); // 30 minutes
    return data;
  }, [getCachedPrediction, setCachedPrediction]);

  // Predict client behavior
  const predictClientBehavior = useCallback(async (
    clientId: string,
    scenario: string = 'purchase_timing'
  ): Promise<ClientBehaviorPrediction> => {
    const cacheKey = `client_${clientId}_${scenario}`;
    const cached = getCachedPrediction(cacheKey);
    if (cached) return cached;

    const response = await fetch('/api/prediction/client-behavior', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: clientId, scenario })
    });

    if (!response.ok) {
      throw new Error('Failed to predict client behavior');
    }

    const data = await response.json();
    setCachedPrediction(cacheKey, data, 1800000); // 30 minutes
    return data;
  }, [getCachedPrediction, setCachedPrediction]);

  // Predict deal outcome
  const predictDealOutcome = useCallback(async (
    dealId: string,
    currentStage: string = 'negotiation'
  ): Promise<DealOutcomePrediction> => {
    const cacheKey = `deal_${dealId}_${currentStage}`;
    const cached = getCachedPrediction(cacheKey);
    if (cached) return cached;

    const response = await fetch('/api/prediction/deal-outcome', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deal_id: dealId, current_stage: currentStage })
    });

    if (!response.ok) {
      throw new Error('Failed to predict deal outcome');
    }

    const data = await response.json();
    setCachedPrediction(cacheKey, data, 900000); // 15 minutes
    return data;
  }, [getCachedPrediction, setCachedPrediction]);

  // Generate business forecast
  const generateBusinessForecast = useCallback(async (
    metricType: string = 'revenue',
    timeframe: 'monthly' | 'quarterly' | 'annual' = 'quarterly'
  ): Promise<BusinessForecast> => {
    const cacheKey = `business_${metricType}_${timeframe}`;
    const cached = getCachedPrediction(cacheKey);
    if (cached) return cached;

    const response = await fetch('/api/prediction/business-forecast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metric_type: metricType, timeframe })
    });

    if (!response.ok) {
      throw new Error('Failed to generate business forecast');
    }

    const data = await response.json();
    setCachedPrediction(cacheKey, data, 3600000); // 1 hour
    return data;
  }, [getCachedPrediction, setCachedPrediction]);

  // Get prediction explanation
  const getPredictionExplanation = useCallback(async (predictionId: string) => {
    const response = await fetch(`/api/prediction/explain/${predictionId}`);

    if (!response.ok) {
      throw new Error('Failed to get prediction explanation');
    }

    return await response.json();
  }, []);

  // Voice-activated prediction request
  const requestPredictionByVoice = useCallback(async (
    command: string,
    context: Record<string, any> = {}
  ) => {
    const matchedCommand = voiceCommands.find(cmd =>
      cmd.patterns.some(pattern =>
        command.toLowerCase().includes(pattern.toLowerCase())
      )
    );

    if (!matchedCommand) {
      throw new Error('Unknown prediction command');
    }

    switch (matchedCommand.action) {
      case 'PREDICT_MARKET_MOVEMENT':
        return await predictMarketMovement(
          context.location || { lat: 0, lng: 0 },
          context.timeframe || 'medium_term'
        );

      case 'PREDICT_CLIENT_BEHAVIOR':
        if (!context.client_id) {
          throw new Error('Client ID required for client behavior prediction');
        }
        return await predictClientBehavior(context.client_id, context.scenario);

      case 'PREDICT_DEAL_OUTCOME':
        if (!context.deal_id) {
          throw new Error('Deal ID required for deal outcome prediction');
        }
        return await predictDealOutcome(context.deal_id, context.current_stage);

      case 'PREDICT_BUSINESS_METRICS':
        return await generateBusinessForecast(
          context.metric_type || 'revenue',
          context.timeframe || 'quarterly'
        );

      default:
        throw new Error('Unsupported prediction command');
    }
  }, [predictMarketMovement, predictClientBehavior, predictDealOutcome, generateBusinessForecast]);

  // Handle real-time prediction updates
  const handlePredictionUpdate = useCallback((prediction: PredictionResult) => {
    setPredictions(prev => ({
      ...prev,
      [prediction.prediction_id]: prediction
    }));

    // Update React Query cache
    queryClient.setQueryData(['prediction', prediction.prediction_id], prediction);

    // Update local cache
    setCachedPrediction(`update_${prediction.prediction_id}`, prediction);
  }, [queryClient, setCachedPrediction]);

  // Handle market alerts
  const handleMarketAlert = useCallback((alert: any) => {
    console.log('Market alert received:', alert);

    // Show notification for critical market changes
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`Market Alert: ${alert.title}`, {
        body: alert.message,
        icon: '/jorge-logo.png',
        tag: 'market-alert'
      });
    }
  }, []);

  // Handle opportunity alerts
  const handleOpportunityAlert = useCallback((opportunity: any) => {
    console.log('Opportunity alert received:', opportunity);

    // Show notification for business opportunities
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`Business Opportunity: ${opportunity.title}`, {
        body: opportunity.description,
        icon: '/jorge-logo.png',
        tag: 'opportunity-alert'
      });
    }
  }, []);

  // Handle risk alerts
  const handleRiskAlert = useCallback((risk: any) => {
    console.log('Risk alert received:', risk);

    // Show notification for risk factors
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`Risk Alert: ${risk.title}`, {
        body: risk.description,
        icon: '/jorge-logo.png',
        tag: 'risk-alert'
      });
    }
  }, []);

  // Bulk prediction requests for dashboard
  const requestBulkPredictions = useCallback(async (requests: PredictionRequest[]) => {
    const response = await fetch('/api/prediction/bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requests })
    });

    if (!response.ok) {
      throw new Error('Failed to process bulk predictions');
    }

    return await response.json();
  }, []);

  // Update prediction accuracy feedback
  const updatePredictionAccuracy = useCallback(async (
    predictionId: string,
    actualOutcome: Record<string, any>
  ) => {
    const response = await fetch('/api/prediction/accuracy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prediction_id: predictionId, actual_outcome: actualOutcome })
    });

    if (!response.ok) {
      throw new Error('Failed to update prediction accuracy');
    }

    return await response.json();
  }, []);

  return {
    // Connection status
    isConnected,

    // Core prediction functions
    predictMarketMovement,
    predictClientBehavior,
    predictDealOutcome,
    generateBusinessForecast,

    // Voice integration
    requestPredictionByVoice,
    voiceCommands,

    // Bulk operations
    requestBulkPredictions,

    // Explanation and accuracy
    getPredictionExplanation,
    updatePredictionAccuracy,

    // Real-time predictions
    predictions,

    // Cache management
    cache: Object.keys(cache).length,
    clearCache: () => setCache({})
  };
};

export default usePredictiveIntelligence;

// Export types for use in components
export type {
  PredictionRequest,
  PredictionResult,
  MarketMovementPrediction,
  ClientBehaviorPrediction,
  DealOutcomePrediction,
  BusinessForecast
};