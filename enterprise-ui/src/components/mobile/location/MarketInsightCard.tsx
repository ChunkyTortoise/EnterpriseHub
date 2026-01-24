'use client';

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  ChartBarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  HomeIcon,
  BanknotesIcon,
  CalendarIcon,
  ClockIcon,
  FireIcon,
  BeakerIcon,
  ShieldCheckIcon,
  AcademicCapIcon,
  BuildingStorefrontIcon,
  MapPinIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";

import useLocationServices from "@/hooks/useLocationServices";
import type { MarketInsight } from "@/lib/location/MarketDataService";

interface MarketInsightCardProps {
  showDetailed?: boolean;
  onViewFullReport?: () => void;
  onNeighborhoodClick?: (neighborhood: string) => void;
}

export function MarketInsightCard({
  showDetailed = false,
  onViewFullReport,
  onNeighborhoodClick,
}: MarketInsightCardProps) {
  const {
    currentLocation,
    marketInsight,
    getMarketInsight,
    getNeighborhoodAnalysis,
    isLoading,
  } = useLocationServices();

  const [analysis, setAnalysis] = useState<any>(null);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number>(0);

  // Auto-refresh market insight when location changes
  useEffect(() => {
    if (currentLocation && (!marketInsight || Date.now() - lastUpdated > 15 * 60 * 1000)) {
      getMarketInsight()
        .then(() => setLastUpdated(Date.now()))
        .catch(console.error);
    }
  }, [currentLocation, marketInsight, getMarketInsight, lastUpdated]);

  // Load neighborhood analysis for detailed view
  useEffect(() => {
    if (showDetailed && currentLocation && !analysis) {
      getNeighborhoodAnalysis()
        .then(setAnalysis)
        .catch(console.error);
    }
  }, [showDetailed, currentLocation, analysis, getNeighborhoodAnalysis]);

  if (!currentLocation) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card text-center py-6"
      >
        <MapPinIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-gray-400">Location required for market insights</p>
      </motion.div>
    );
  }

  if (isLoading && !marketInsight) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card text-center py-6"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-jorge-electric border-t-transparent rounded-full mx-auto mb-3"
        />
        <p className="text-sm text-gray-400">Loading market insights...</p>
      </motion.div>
    );
  }

  if (!marketInsight) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card text-center py-6"
      >
        <ChartBarIcon className="w-8 h-8 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-gray-400 mb-2">Market data unavailable</p>
        <button
          onClick={() => getMarketInsight()}
          className="px-3 py-1 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
        >
          Retry
        </button>
      </motion.div>
    );
  }

  const getVelocityColor = (velocity: string) => {
    switch (velocity) {
      case 'hot':
        return 'text-red-400';
      case 'warm':
        return 'text-orange-400';
      case 'balanced':
        return 'text-jorge-glow';
      case 'slow':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  const getVelocityIcon = (velocity: string) => {
    switch (velocity) {
      case 'hot':
        return FireIcon;
      case 'warm':
        return TrendingUpIcon;
      case 'balanced':
        return ChartBarIcon;
      case 'slow':
        return ClockIcon;
      default:
        return ChartBarIcon;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return TrendingUpIcon;
      case 'decreasing':
        return TrendingDownIcon;
      default:
        return ChartBarIcon;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return 'text-jorge-glow';
      case 'decreasing':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    if (price >= 1000) {
      return `$${(price / 1000).toFixed(0)}K`;
    }
    return `$${price.toLocaleString()}`;
  };

  const formatPercentage = (value: number, showSign = true) => {
    const sign = showSign && value > 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  const VelocityIcon = getVelocityIcon(marketInsight.marketData.marketVelocity);
  const TrendIcon = getTrendIcon(marketInsight.marketData.appreciationTrend);

  return (
    <div className="space-y-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <ChartBarIcon className="w-5 h-5 text-jorge-electric" />
          <h2 className="jorge-heading text-lg">Market Intelligence</h2>
        </div>
        <button
          onClick={() => onNeighborhoodClick?.(marketInsight.neighborhood)}
          className="px-2 py-1 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
        >
          {marketInsight.neighborhood.toUpperCase()}
        </button>
      </motion.div>

      {/* Quick Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card"
      >
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center">
            <div className="property-value text-lg">
              {formatPrice(marketInsight.marketData.medianPrice)}
            </div>
            <div className="text-xs text-gray-400">Median Price</div>
          </div>
          <div className="text-center">
            <div className="property-value text-lg">
              ${marketInsight.marketData.pricePerSqft}
            </div>
            <div className="text-xs text-gray-400">Per SqFt</div>
          </div>
          <div className="text-center">
            <div className="property-value text-lg">
              {marketInsight.marketData.averageDaysOnMarket}
            </div>
            <div className="text-xs text-gray-400">Avg Days</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-bold ${getVelocityColor(marketInsight.marketData.marketVelocity)}`}>
              {marketInsight.marketData.marketVelocity.toUpperCase()}
            </div>
            <div className="text-xs text-gray-400">Market</div>
          </div>
        </div>

        {/* Market Velocity Indicator */}
        <div className="flex items-center justify-center gap-2 p-3 bg-white/5 rounded-lg">
          <VelocityIcon className={`w-5 h-5 ${getVelocityColor(marketInsight.marketData.marketVelocity)}`} />
          <span className={`text-sm font-medium ${getVelocityColor(marketInsight.marketData.marketVelocity)}`}>
            {marketInsight.marketData.marketVelocity.charAt(0).toUpperCase() +
             marketInsight.marketData.marketVelocity.slice(1)} Market
          </span>
          <div className={`ml-2 flex items-center gap-1 text-xs ${getTrendColor(marketInsight.marketData.appreciationTrend)}`}>
            <TrendIcon className="w-3 h-3" />
            {marketInsight.marketData.appreciationTrend}
          </div>
        </div>
      </motion.div>

      {/* Price Trends */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="jorge-card"
      >
        <h3 className="jorge-heading text-base mb-3 flex items-center gap-2">
          <TrendingUpIcon className="w-4 h-4 text-jorge-glow" />
          Price Trends
        </h3>

        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="text-center">
            <div className={`text-sm font-semibold ${
              marketInsight.marketData.priceChange30Day >= 0 ? 'text-jorge-glow' : 'text-red-400'
            }`}>
              {formatPercentage(marketInsight.marketData.priceChange30Day)}
            </div>
            <div className="text-gray-400">30 Days</div>
          </div>
          <div className="text-center">
            <div className={`text-sm font-semibold ${
              marketInsight.marketData.priceChange90Day >= 0 ? 'text-jorge-glow' : 'text-red-400'
            }`}>
              {formatPercentage(marketInsight.marketData.priceChange90Day)}
            </div>
            <div className="text-gray-400">90 Days</div>
          </div>
          <div className="text-center">
            <div className={`text-sm font-semibold ${
              marketInsight.marketData.priceChangeYoY >= 0 ? 'text-jorge-glow' : 'text-red-400'
            }`}>
              {formatPercentage(marketInsight.marketData.priceChangeYoY)}
            </div>
            <div className="text-gray-400">Year</div>
          </div>
        </div>

        {/* Additional Metrics */}
        <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-white/10 text-xs">
          <div className="text-center">
            <div className="text-sm text-white font-medium">
              {marketInsight.marketData.salesVolume30Day}
            </div>
            <div className="text-gray-400">Sales (30d)</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-jorge-electric font-medium">
              {marketInsight.marketData.demandScore}/100
            </div>
            <div className="text-gray-400">Demand Score</div>
          </div>
        </div>
      </motion.div>

      {/* Investment Insight */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="jorge-card"
      >
        <h3 className="jorge-heading text-base mb-3 flex items-center gap-2">
          <BanknotesIcon className="w-4 h-4 text-jorge-gold" />
          Investment Outlook
        </h3>

        <div className="grid grid-cols-2 gap-4 mb-3">
          <div className="text-center">
            <div className="property-value text-base">
              {marketInsight.investment.investmentScore}/100
            </div>
            <div className="text-xs text-gray-400">Investment Score</div>
          </div>
          <div className="text-center">
            <div className="property-value text-base text-jorge-glow">
              {formatPercentage(marketInsight.investment.appreciation5Year, false)}
            </div>
            <div className="text-xs text-gray-400">5-Yr Growth</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="text-center">
            <div className="text-sm text-jorge-electric font-medium">
              {formatPercentage(marketInsight.investment.rentalYield, false)}
            </div>
            <div className="text-gray-400">Rental Yield</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-jorge-gold font-medium">
              {marketInsight.investment.flipPotential}/100
            </div>
            <div className="text-gray-400">Flip Score</div>
          </div>
          <div className="text-center">
            <div className={`text-sm font-medium ${
              marketInsight.investment.recommendation === 'strong_buy' ? 'text-jorge-glow' :
              marketInsight.investment.recommendation === 'buy' ? 'text-blue-400' :
              marketInsight.investment.recommendation === 'hold' ? 'text-yellow-400' : 'text-red-400'
            }`}>
              {marketInsight.investment.recommendation.replace(/_/g, ' ').toUpperCase()}
            </div>
            <div className="text-gray-400">Recommendation</div>
          </div>
        </div>
      </motion.div>

      {/* Detailed Analysis */}
      {showDetailed && analysis && (
        <>
          {/* Neighborhood Analysis */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="jorge-card"
          >
            <h3 className="jorge-heading text-base mb-3">Neighborhood Analysis</h3>
            <p className="text-sm text-gray-300 mb-3 leading-relaxed">
              {analysis.overview}
            </p>

            {analysis.strengths && analysis.strengths.length > 0 && (
              <div className="mb-3">
                <h4 className="text-sm font-medium text-jorge-glow mb-2">Strengths:</h4>
                <ul className="space-y-1">
                  {analysis.strengths.slice(0, 3).map((strength: string, index: number) => (
                    <li key={index} className="flex items-start gap-2 text-xs text-gray-300">
                      <div className="w-1 h-1 bg-jorge-glow rounded-full mt-2" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {analysis.opportunities && analysis.opportunities.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-jorge-electric mb-2">Opportunities:</h4>
                <ul className="space-y-1">
                  {analysis.opportunities.slice(0, 2).map((opportunity: string, index: number) => (
                    <li key={index} className="flex items-start gap-2 text-xs text-gray-300">
                      <div className="w-1 h-1 bg-jorge-electric rounded-full mt-2" />
                      {opportunity}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>

          {/* Quality Indicators */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="jorge-card"
          >
            <h3 className="jorge-heading text-base mb-3">Quality Indicators</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-jorge-glow/20 rounded-lg">
                  <ShieldCheckIcon className="w-4 h-4 text-jorge-glow" />
                </div>
                <div>
                  <div className="text-sm text-white font-medium">
                    {marketInsight.safety.crimeScore}/100
                  </div>
                  <div className="text-xs text-gray-400">Safety Score</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-jorge-electric/20 rounded-lg">
                  <AcademicCapIcon className="w-4 h-4 text-jorge-electric" />
                </div>
                <div>
                  <div className="text-sm text-white font-medium">
                    {marketInsight.schools.length > 0
                      ? (marketInsight.schools.reduce((sum, school) => sum + school.rating, 0) / marketInsight.schools.length).toFixed(1)
                      : 'N/A'
                    }/10
                  </div>
                  <div className="text-xs text-gray-400">School Rating</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-jorge-gold/20 rounded-lg">
                  <BuildingStorefrontIcon className="w-4 h-4 text-jorge-gold" />
                </div>
                <div>
                  <div className="text-sm text-white font-medium">
                    {marketInsight.amenities.walkScore}/100
                  </div>
                  <div className="text-xs text-gray-400">Walk Score</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <BeakerIcon className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <div className="text-sm text-white font-medium">
                    {analysis.marketPosition?.toUpperCase() || 'MID'}
                  </div>
                  <div className="text-xs text-gray-400">Market Tier</div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: showDetailed ? 0.5 : 0.3 }}
        className="grid grid-cols-2 gap-3"
      >
        {!showDetailed && (
          <button
            onClick={onViewFullReport}
            className="flex items-center justify-center gap-2 py-3 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
          >
            <InformationCircleIcon className="w-4 h-4" />
            FULL REPORT
          </button>
        )}

        <button
          onClick={() => getMarketInsight()}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 py-3 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic disabled:opacity-50"
        >
          {isLoading ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-3 h-3 border border-jorge-glow border-t-transparent rounded-full"
            />
          ) : (
            <ChartBarIcon className="w-4 h-4" />
          )}
          {isLoading ? 'UPDATING...' : 'REFRESH'}
        </button>
      </motion.div>

      {/* Last Updated */}
      <div className="text-center text-xs text-gray-500">
        Last updated: {new Date(marketInsight.lastUpdated).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        })}
      </div>
    </div>
  );
}