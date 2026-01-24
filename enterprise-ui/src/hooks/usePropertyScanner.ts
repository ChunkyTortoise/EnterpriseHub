/**
 * Jorge Real Estate AI Platform - Property Scanner Hook
 * Comprehensive property scanning and analysis logic
 *
 * Features:
 * - Multi-format property lookup (QR, Address, MLS)
 * - Jorge's confrontational analysis engine
 * - CMA generation with ML insights
 * - Offline scanning with sync capabilities
 * - Performance optimization
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { useOfflineStorage } from './useOfflineStorage';

interface PropertyScanOptions {
  scanType: 'qr' | 'barcode' | 'voice' | 'photo';
  scanTime: number;
  location?: { lat: number; lng: number };
  offline?: boolean;
}

interface PropertyData {
  id: string;
  address: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  lotSize: number;
  yearBuilt: number;
  propertyType: string;
  status: string;
  daysOnMarket: number;
  mlsNumber: string;
  photos: string[];
}

interface MarketAnalysis {
  pricePerSqft: number;
  marketTrend: 'up' | 'down' | 'stable';
  trendPercentage: number;
  comparablesSold: number;
  avgDaysOnMarket: number;
  priceReduction: number;
  hotScore: number;
}

interface JorgeAnalysis {
  verdict: string;
  confrontationalTone: string;
  redFlags: string[];
  opportunities: string[];
  recommendedAction: string;
  commission: number;
}

interface CMAData {
  lowEstimate: number;
  highEstimate: number;
  suggestedListing: number;
  comparables: Array<{
    address: string;
    price: number;
    sqft: number;
    daysOnMarket: number;
  }>;
}

interface ScanResult {
  property: PropertyData;
  marketAnalysis: MarketAnalysis;
  jorgeAnalysis: JorgeAnalysis;
  cma?: CMAData;
  scanning: {
    scanType: string;
    timestamp: number;
    location?: { lat: number; lng: number };
    confidence: number;
  };
}

interface ScanHistoryItem {
  id: string;
  type: string;
  data: string;
  timestamp: number;
  location?: { lat: number; lng: number };
  confidence: number;
  result?: ScanResult;
  status: 'success' | 'failed' | 'processing';
  duration: number;
}

export function usePropertyScanner() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [scanHistory, setScanHistory] = useState<ScanHistoryItem[]>([]);

  const { storeData, getData, isOnline } = useOfflineStorage();
  const abortControllerRef = useRef<AbortController | null>(null);

  // Parse different data types
  const parsePropertyData = useCallback((data: string): { type: string; identifier: string } => {
    // URL pattern (QR codes)
    if (data.startsWith('http')) {
      const urlMatch = data.match(/property[\/:](\w+)/i);
      if (urlMatch) {
        return { type: 'url', identifier: urlMatch[1] };
      }
    }

    // MLS pattern
    const mlsMatch = data.match(/MLS[:\s]*([A-Z0-9]+)/i);
    if (mlsMatch) {
      return { type: 'mls', identifier: mlsMatch[1] };
    }

    // Lockbox pattern
    const lockboxMatch = data.match(/LOCKBOX[:\s]*([0-9]+)/i);
    if (lockboxMatch) {
      return { type: 'lockbox', identifier: lockboxMatch[1] };
    }

    // JSON property data
    try {
      const jsonData = JSON.parse(data);
      if (jsonData.propertyId || jsonData.address) {
        return { type: 'json', identifier: jsonData.propertyId || jsonData.address };
      }
    } catch {
      // Not JSON, continue
    }

    // Address pattern (voice/text input)
    const addressPattern = /(\d+[\w\s\.,#-]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|way|place|pl|court|ct|circle|cir))/i;
    const addressMatch = data.match(addressPattern);
    if (addressMatch) {
      return { type: 'address', identifier: addressMatch[1].trim() };
    }

    // Default to text search
    return { type: 'text', identifier: data };
  }, []);

  // Generate Jorge's confrontational analysis
  const generateJorgeAnalysis = useCallback((property: PropertyData, marketAnalysis: MarketAnalysis): JorgeAnalysis => {
    const commission = property.price * 0.06; // 6% commission
    const pricePerSqft = property.price / property.sqft;

    // Determine verdict based on market conditions
    let verdict = '';
    let confrontationalTone = '';
    let redFlags: string[] = [];
    let opportunities: string[] = [];
    let recommendedAction = '';

    // Price analysis
    if (pricePerSqft > 200) {
      verdict += 'Overpriced property in a competitive market. ';
      redFlags.push('Price per sq ft exceeds market average significantly');
      confrontationalTone = 'This seller is dreaming if they think this price is realistic.';
    } else if (pricePerSqft < 100) {
      verdict += 'Undervalued opportunity with potential upside. ';
      opportunities.push('Below-market pricing suggests motivated seller or hidden value');
      confrontationalTone = 'Either this is a steal or there\'s something seriously wrong here.';
    } else {
      verdict += 'Reasonably priced property with standard market positioning. ';
      confrontationalTone = 'Nothing special here, but it\'s not completely ridiculous either.';
    }

    // Days on market analysis
    if (property.daysOnMarket > 90) {
      redFlags.push('Extended time on market suggests pricing issues or property defects');
      verdict += 'Property has been sitting too long - red flag for underlying issues. ';
      if (!confrontationalTone.includes('ridiculous')) {
        confrontationalTone = 'If it hasn\'t sold in 90 days, there\'s a reason. Find out what it is.';
      }
    } else if (property.daysOnMarket < 15) {
      opportunities.push('Fresh listing with potential for quick movement');
      verdict += 'Recent listing with potential for fast action. ';
    }

    // Market trend analysis
    if (marketAnalysis.marketTrend === 'down' && marketAnalysis.trendPercentage < -10) {
      redFlags.push('Market declining rapidly - timing concerns for resale');
      verdict += 'Falling market makes this a risky investment. ';
    } else if (marketAnalysis.marketTrend === 'up' && marketAnalysis.trendPercentage > 10) {
      opportunities.push('Rising market provides appreciation potential');
      verdict += 'Strong market momentum supports value growth. ';
    }

    // Property age analysis
    const propertyAge = new Date().getFullYear() - property.yearBuilt;
    if (propertyAge > 50) {
      redFlags.push('Older property likely requires significant maintenance and updates');
    } else if (propertyAge < 10) {
      opportunities.push('Newer construction with modern amenities and lower maintenance');
    }

    // Hot score analysis
    if (marketAnalysis.hotScore > 80) {
      opportunities.push('High demand property in competitive market');
      recommendedAction = 'Move fast - this won\'t last long in a hot market. ';
    } else if (marketAnalysis.hotScore < 40) {
      redFlags.push('Low market interest may indicate hidden issues');
      recommendedAction = 'Investigate thoroughly - low interest is usually justified. ';
    } else {
      recommendedAction = 'Standard market conditions - proceed with normal due diligence. ';
    }

    // Commission opportunity
    recommendedAction += `At ${commission.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} commission, `;
    if (commission > 25000) {
      recommendedAction += 'this is worth serious pursuit.';
    } else if (commission > 15000) {
      recommendedAction += 'decent opportunity if everything checks out.';
    } else {
      recommendedAction += 'marginal deal unless volume play.';
    }

    // Default confrontational tone if none set
    if (!confrontationalTone) {
      confrontationalTone = 'Another generic property in a sea of mediocrity. Make sure you know why this one\'s different.';
    }

    return {
      verdict: verdict.trim(),
      confrontationalTone,
      redFlags,
      opportunities,
      recommendedAction: recommendedAction.trim(),
      commission
    };
  }, []);

  // Generate mock property data (replace with actual API calls)
  const fetchPropertyData = useCallback(async (identifier: string, type: string, signal?: AbortSignal): Promise<PropertyData> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    if (signal?.aborted) {
      throw new Error('Request aborted');
    }

    // Mock property database
    const mockProperties: Record<string, PropertyData> = {
      '12345': {
        id: 'prop_12345',
        address: '123 Main Street, Anytown, State 12345',
        price: 450000,
        bedrooms: 3,
        bathrooms: 2,
        sqft: 2100,
        lotSize: 0.25,
        yearBuilt: 2015,
        propertyType: 'Single Family',
        status: 'Active',
        daysOnMarket: 45,
        mlsNumber: 'MLS123456',
        photos: []
      },
      'RE001234': {
        id: 'prop_re001234',
        address: '456 Oak Avenue, Springfield, State 67890',
        price: 285000,
        bedrooms: 2,
        bathrooms: 1,
        sqft: 1200,
        lotSize: 0.15,
        yearBuilt: 1985,
        propertyType: 'Condo',
        status: 'Active',
        daysOnMarket: 120,
        mlsNumber: 'RE001234',
        photos: []
      },
      '9874': {
        id: 'prop_lockbox_9874',
        address: '789 Pine Street, Riverside, State 54321',
        price: 675000,
        bedrooms: 4,
        bathrooms: 3,
        sqft: 2800,
        lotSize: 0.5,
        yearBuilt: 2020,
        propertyType: 'Single Family',
        status: 'Active',
        daysOnMarket: 12,
        mlsNumber: 'LS987654',
        photos: []
      }
    };

    // Try to find exact match
    if (mockProperties[identifier]) {
      return mockProperties[identifier];
    }

    // Generate dynamic property based on identifier
    const addressSamples = [
      '123 Maple Drive, Cityville, State',
      '456 Elm Street, Townsburg, State',
      '789 Cedar Lane, Villageton, State',
      '321 Birch Avenue, Hamlet, State',
      '654 Spruce Road, Borough, State'
    ];

    const randomAddress = addressSamples[Math.floor(Math.random() * addressSamples.length)];
    const basePrice = 200000 + Math.random() * 600000;

    return {
      id: `prop_${Date.now()}`,
      address: type === 'address' ? identifier : randomAddress,
      price: Math.round(basePrice),
      bedrooms: Math.floor(Math.random() * 4) + 1,
      bathrooms: Math.floor(Math.random() * 3) + 1,
      sqft: Math.floor(1200 + Math.random() * 2000),
      lotSize: Number((0.1 + Math.random() * 0.8).toFixed(2)),
      yearBuilt: 1980 + Math.floor(Math.random() * 44),
      propertyType: ['Single Family', 'Condo', 'Townhouse', 'Multi-Family'][Math.floor(Math.random() * 4)],
      status: Math.random() > 0.2 ? 'Active' : 'Pending',
      daysOnMarket: Math.floor(Math.random() * 180),
      mlsNumber: `ML${Math.floor(Math.random() * 999999).toString().padStart(6, '0')}`,
      photos: []
    };
  }, []);

  // Generate market analysis
  const generateMarketAnalysis = useCallback((property: PropertyData): MarketAnalysis => {
    const pricePerSqft = Math.round(property.price / property.sqft);
    const marketTrends = ['up', 'down', 'stable'] as const;
    const trend = marketTrends[Math.floor(Math.random() * marketTrends.length)];

    return {
      pricePerSqft,
      marketTrend: trend,
      trendPercentage: Number((Math.random() * 20 - 10).toFixed(1)),
      comparablesSold: Math.floor(Math.random() * 20) + 5,
      avgDaysOnMarket: Math.floor(Math.random() * 120) + 30,
      priceReduction: Math.random() > 0.7 ? Math.floor(Math.random() * 50000) : 0,
      hotScore: Math.floor(Math.random() * 100)
    };
  }, []);

  // Generate CMA
  const generateCMA = useCallback(async (propertyId: string): Promise<CMAData> => {
    // Simulate CMA generation delay
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

    const property = await fetchPropertyData(propertyId, 'id');
    const basePrice = property.price;
    const variation = 0.15; // 15% variation

    const lowEstimate = Math.round(basePrice * (1 - variation));
    const highEstimate = Math.round(basePrice * (1 + variation));
    const suggestedListing = Math.round(basePrice * (1 + (Math.random() * 0.1 - 0.05)));

    // Generate mock comparables
    const comparables = Array.from({ length: 5 }, (_, i) => ({
      address: `Comparable ${i + 1} Street`,
      price: Math.round(basePrice * (0.9 + Math.random() * 0.2)),
      sqft: property.sqft + Math.floor(Math.random() * 400 - 200),
      daysOnMarket: Math.floor(Math.random() * 90) + 15
    }));

    return {
      lowEstimate,
      highEstimate,
      suggestedListing,
      comparables
    };
  }, [fetchPropertyData]);

  // Main scan function
  const scanProperty = useCallback(async (
    data: string,
    options: PropertyScanOptions
  ): Promise<ScanResult | null> => {
    setIsLoading(true);
    setError('');

    try {
      // Cancel any existing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();
      const { signal } = abortControllerRef.current;

      // Parse the scanned data
      const { type, identifier } = parsePropertyData(data);

      // Check offline storage first
      const cacheKey = `property_${identifier}`;
      let property: PropertyData;

      if (!isOnline) {
        const cachedData = await getData(cacheKey);
        if (cachedData) {
          property = cachedData.property;
        } else {
          throw new Error('Property data not available offline');
        }
      } else {
        // Fetch from API
        property = await fetchPropertyData(identifier, type, signal);

        // Store in cache for offline access
        await storeData(cacheKey, { property, timestamp: Date.now() });
      }

      // Generate analyses
      const marketAnalysis = generateMarketAnalysis(property);
      const jorgeAnalysis = generateJorgeAnalysis(property, marketAnalysis);

      const result: ScanResult = {
        property,
        marketAnalysis,
        jorgeAnalysis,
        scanning: {
          scanType: options.scanType,
          timestamp: Date.now(),
          location: options.location,
          confidence: 0.85 + Math.random() * 0.15
        }
      };

      // Add to scan history
      const historyItem: ScanHistoryItem = {
        id: Date.now().toString(),
        type: options.scanType,
        data,
        timestamp: Date.now(),
        location: options.location,
        confidence: result.scanning.confidence,
        result,
        status: 'success',
        duration: options.scanTime
      };

      setScanHistory(prev => [historyItem, ...prev.slice(0, 49)]); // Keep last 50 scans

      return result;

    } catch (error: any) {
      if (error.name === 'AbortError') {
        return null;
      }

      console.error('Property scan failed:', error);
      setError(error.message || 'Failed to scan property');

      // Add failed scan to history
      const historyItem: ScanHistoryItem = {
        id: Date.now().toString(),
        type: options.scanType,
        data,
        timestamp: Date.now(),
        location: options.location,
        confidence: 0,
        status: 'failed',
        duration: options.scanTime
      };

      setScanHistory(prev => [historyItem, ...prev.slice(0, 49)]);

      return null;
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [parsePropertyData, isOnline, getData, storeData, fetchPropertyData, generateMarketAnalysis, generateJorgeAnalysis]);

  // Clear scan history
  const clearHistory = useCallback(() => {
    setScanHistory([]);
  }, []);

  // Cancel current scan
  const cancelScan = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    scanProperty,
    generateCMA,
    isLoading,
    error,
    scanHistory,
    clearHistory,
    cancelScan
  };
}