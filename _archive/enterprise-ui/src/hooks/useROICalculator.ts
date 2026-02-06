// React Hook for ROI Calculator and Value Proposition Engine
// Manages state and calculations for Jorge's client presentation system

'use client';

import { useState, useCallback, useMemo } from 'react';
import { ROIEngine, type ClientProfile, type ROICalculation } from '@/lib/presentation/ROIEngine';
import { ValueEngine, type ValueNarrative, type ValuePresentation } from '@/lib/presentation/ValueEngine';

interface ROICalculatorState {
  clientProfile: ClientProfile | null;
  roiCalculation: ROICalculation | null;
  valueNarrative: ValueNarrative | null;
  valuePresentation: ValuePresentation | null;
  isCalculating: boolean;
  error: string | null;
}

export interface ROICalculatorActions {
  setClientProfile: (profile: ClientProfile) => void;
  updateProperty: (property: Partial<ClientProfile>) => void;
  calculateROI: (timeHorizonMonths?: number) => void;
  generatePresentation: () => void;
  resetCalculator: () => void;
  exportToJSON: () => string;
  exportToPDF: () => Promise<void>;
}

export function useROICalculator() {
  const [state, setState] = useState<ROICalculatorState>({
    clientProfile: null,
    roiCalculation: null,
    valueNarrative: null,
    valuePresentation: null,
    isCalculating: false,
    error: null,
  });

  // Set client profile and trigger recalculation
  const setClientProfile = useCallback((profile: ClientProfile) => {
    setState(prev => ({
      ...prev,
      clientProfile: profile,
      roiCalculation: null,
      valueNarrative: null,
      valuePresentation: null,
      error: null,
    }));
  }, []);

  // Update specific profile properties
  const updateProperty = useCallback((updates: Partial<ClientProfile>) => {
    setState(prev => {
      if (!prev.clientProfile) return prev;

      const updatedProfile = { ...prev.clientProfile, ...updates };

      return {
        ...prev,
        clientProfile: updatedProfile,
        roiCalculation: null,
        valueNarrative: null,
        valuePresentation: null,
      };
    });
  }, []);

  // Calculate ROI with current profile
  const calculateROI = useCallback(async (timeHorizonMonths = 12) => {
    if (!state.clientProfile) {
      setState(prev => ({ ...prev, error: 'Client profile required for ROI calculation' }));
      return;
    }

    setState(prev => ({ ...prev, isCalculating: true, error: null }));

    try {
      // Simulate calculation delay for better UX
      await new Promise(resolve => setTimeout(resolve, 500));

      const roiCalculation = ROIEngine.calculateROI(state.clientProfile, timeHorizonMonths);

      setState(prev => ({
        ...prev,
        roiCalculation,
        isCalculating: false,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to calculate ROI',
        isCalculating: false,
      }));
    }
  }, [state.clientProfile]);

  // Generate complete value presentation
  const generatePresentation = useCallback(() => {
    if (!state.clientProfile || !state.roiCalculation) {
      setState(prev => ({ ...prev, error: 'Profile and ROI calculation required' }));
      return;
    }

    try {
      const valueNarrative = ValueEngine.generateValueNarrative(
        state.clientProfile,
        state.roiCalculation
      );

      const valuePresentation = ValueEngine.generatePresentation(
        state.clientProfile,
        state.roiCalculation,
        valueNarrative
      );

      setState(prev => ({
        ...prev,
        valueNarrative,
        valuePresentation,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to generate presentation',
      }));
    }
  }, [state.clientProfile, state.roiCalculation]);

  // Reset calculator to initial state
  const resetCalculator = useCallback(() => {
    setState({
      clientProfile: null,
      roiCalculation: null,
      valueNarrative: null,
      valuePresentation: null,
      isCalculating: false,
      error: null,
    });
  }, []);

  // Export data as JSON
  const exportToJSON = useCallback(() => {
    const exportData = {
      timestamp: new Date().toISOString(),
      clientProfile: state.clientProfile,
      roiCalculation: state.roiCalculation,
      valueNarrative: state.valueNarrative,
      version: '1.0.0',
    };

    return JSON.stringify(exportData, null, 2);
  }, [state]);

  // Export presentation as PDF
  const exportToPDF = useCallback(async () => {
    if (!state.valuePresentation) {
      throw new Error('No presentation to export');
    }

    // This would integrate with a PDF generation library
    // For now, we'll create a downloadable JSON
    const data = exportToJSON();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `jorge-roi-${state.clientProfile?.name || 'client'}-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }, [state.valuePresentation, exportToJSON, state.clientProfile]);

  // Memoized computed values
  const computedValues = useMemo(() => {
    const { roiCalculation } = state;

    if (!roiCalculation) {
      return {
        roiMultiple: 0,
        netBenefit: 0,
        breakEvenMonths: 0,
        isPositiveROI: false,
        confidenceLevel: 'low' as const,
      };
    }

    const additionalCost = roiCalculation.jorgeAICosts.total - roiCalculation.traditionalCosts.total;
    const roiMultiple = roiCalculation.jorgeAIBenefits.total / Math.abs(additionalCost);
    const isPositiveROI = roiCalculation.netROI > 0;

    let confidenceLevel: 'low' | 'medium' | 'high' = 'medium';
    if (roiMultiple >= 3) confidenceLevel = 'high';
    else if (roiMultiple < 1.5) confidenceLevel = 'low';

    return {
      roiMultiple,
      netBenefit: roiCalculation.netROI,
      breakEvenMonths: roiCalculation.breakEvenMonths,
      isPositiveROI,
      confidenceLevel,
    };
  }, [state.roiCalculation]);

  // Memoized presentation status
  const presentationStatus = useMemo(() => {
    const hasProfile = !!state.clientProfile;
    const hasCalculation = !!state.roiCalculation;
    const hasPresentation = !!state.valuePresentation;

    return {
      hasProfile,
      hasCalculation,
      hasPresentation,
      isReady: hasProfile && hasCalculation && hasPresentation,
      completionPercentage: [hasProfile, hasCalculation, hasPresentation].filter(Boolean).length * 33.33,
    };
  }, [state.clientProfile, state.roiCalculation, state.valuePresentation]);

  // Actions object
  const actions: ROICalculatorActions = {
    setClientProfile,
    updateProperty,
    calculateROI,
    generatePresentation,
    resetCalculator,
    exportToJSON,
    exportToPDF,
  };

  return {
    // State
    ...state,

    // Computed values
    ...computedValues,

    // Status
    ...presentationStatus,

    // Actions
    ...actions,
  };
}

// Preset client profiles for quick demos
export const useROIPresets = () => {
  return useMemo(() => ({
    luxuryClient: ROIEngine.generateClientProfile(
      "Patricia Williams",
      2500000,
      "luxury",
      "high"
    ),
    midMarketClient: ROIEngine.generateClientProfile(
      "Mike Johnson",
      450000,
      "mid-market",
      "medium"
    ),
    firstTimeClient: ROIEngine.generateClientProfile(
      "Sarah & David Chen",
      320000,
      "first-time",
      "low"
    ),
    investorClient: ROIEngine.generateClientProfile(
      "Robert Martinez",
      750000,
      "investor",
      "high"
    ),
  }), []);
};

// Market segment insights
export const useMarketInsights = (segment?: ClientProfile['marketSegment']) => {
  return useMemo(() => {
    const insights = {
      luxury: {
        avgPropertyValue: 2500000,
        avgDaysOnMarket: 45,
        priceVolatility: 'high',
        keyFactors: ['Privacy', 'Speed', 'White-glove service', 'Proven results'],
        jorgeAdvantage: 'AI discretion with premium results',
      },
      'mid-market': {
        avgPropertyValue: 450000,
        avgDaysOnMarket: 35,
        priceVolatility: 'medium',
        keyFactors: ['Value', 'Reliability', 'Communication', 'Fair pricing'],
        jorgeAdvantage: 'Professional service at every price point',
      },
      'first-time': {
        avgPropertyValue: 320000,
        avgDaysOnMarket: 40,
        priceVolatility: 'low',
        keyFactors: ['Education', 'Guidance', 'Simplicity', 'Trust'],
        jorgeAdvantage: 'AI-powered education and guidance',
      },
      investor: {
        avgPropertyValue: 750000,
        avgDaysOnMarket: 25,
        priceVolatility: 'medium',
        keyFactors: ['ROI', 'Speed', 'Data', 'Market intelligence'],
        jorgeAdvantage: 'Data-driven insights for portfolio optimization',
      },
    };

    return segment ? insights[segment] : insights;
  }, [segment]);
};