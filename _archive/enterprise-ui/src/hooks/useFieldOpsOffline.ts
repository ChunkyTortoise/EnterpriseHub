/**
 * useFieldOpsOffline — React hook for Week 5-8 offline field operations
 *
 * Provides offline-first data access for field agents:
 * - Market snapshots cached in IndexedDB
 * - Propensity scores with background refresh
 * - Compliance results history
 * - Export reports for offline viewing
 *
 * Falls back to IndexedDB cache when offline, syncs when online.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  fieldOpsStore,
  type MarketSnapshot,
  type PropensityScoreCache,
  type ComplianceResultCache,
  type ExportReportCache,
} from '@/lib/offline/FieldOpsOfflineStore';

interface UseFieldOpsOfflineReturn {
  // Market data
  marketSnapshot: MarketSnapshot | null;
  fetchMarketSnapshot: (neighborhood: string) => Promise<MarketSnapshot | null>;
  allMarketSnapshots: MarketSnapshot[];
  refreshMarketData: () => Promise<void>;

  // Propensity
  propensityScore: PropensityScoreCache | null;
  fetchPropensityScore: (contactId: string) => Promise<PropensityScoreCache | null>;
  hotLeads: PropensityScoreCache[];
  refreshHotLeads: () => Promise<void>;

  // Compliance
  complianceHistory: ComplianceResultCache[];
  fetchComplianceHistory: (contactId: string) => Promise<void>;

  // Reports
  exportReports: ExportReportCache[];
  refreshExportReports: () => Promise<void>;

  // Meta
  isOnline: boolean;
  storageStats: Record<string, number> | null;
  purgeExpired: () => Promise<number>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useFieldOpsOffline(): UseFieldOpsOfflineReturn {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true,
  );
  const [marketSnapshot, setMarketSnapshot] = useState<MarketSnapshot | null>(null);
  const [allMarketSnapshots, setAllMarketSnapshots] = useState<MarketSnapshot[]>([]);
  const [propensityScore, setPropensityScore] = useState<PropensityScoreCache | null>(null);
  const [hotLeads, setHotLeads] = useState<PropensityScoreCache[]>([]);
  const [complianceHistory, setComplianceHistory] = useState<ComplianceResultCache[]>([]);
  const [exportReports, setExportReports] = useState<ExportReportCache[]>([]);
  const [storageStats, setStorageStats] = useState<Record<string, number> | null>(null);

  const mounted = useRef(true);

  // Network monitoring
  useEffect(() => {
    const goOnline = () => setIsOnline(true);
    const goOffline = () => setIsOnline(false);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      mounted.current = false;
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  // --- Market Snapshot ---

  const fetchMarketSnapshot = useCallback(
    async (neighborhood: string): Promise<MarketSnapshot | null> => {
      // Try cache first
      const cached = await fieldOpsStore.getMarketSnapshot(neighborhood);

      if (isOnline) {
        try {
          const resp = await fetch(
            `${API_BASE}/api/v1/rc-market/snapshot/${neighborhood}`,
          );
          if (resp.ok) {
            const data = await resp.json();
            await fieldOpsStore.saveMarketSnapshot(data);
            if (mounted.current) setMarketSnapshot(data);
            return data;
          }
        } catch {
          // Fall through to cache
        }
      }

      if (cached && mounted.current) setMarketSnapshot(cached);
      return cached;
    },
    [isOnline],
  );

  const refreshMarketData = useCallback(async () => {
    const snapshots = await fieldOpsStore.getAllMarketSnapshots();
    if (mounted.current) setAllMarketSnapshots(snapshots);

    const stats = await fieldOpsStore.getStorageStats();
    if (mounted.current) setStorageStats(stats);
  }, []);

  // --- Propensity Score ---

  const fetchPropensityScore = useCallback(
    async (contactId: string): Promise<PropensityScoreCache | null> => {
      const cached = await fieldOpsStore.getPropensityScore(contactId);

      if (isOnline) {
        try {
          const resp = await fetch(`${API_BASE}/api/v1/propensity/score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contact_id: contactId }),
          });
          if (resp.ok) {
            const data = await resp.json();
            await fieldOpsStore.savePropensityScore(data);
            if (mounted.current) setPropensityScore(data);
            return data;
          }
        } catch {
          // Fall through to cache
        }
      }

      if (cached && mounted.current) setPropensityScore(cached);
      return cached;
    },
    [isOnline],
  );

  const refreshHotLeads = useCallback(async () => {
    const leads = await fieldOpsStore.getHotLeads();
    if (mounted.current) setHotLeads(leads);
  }, []);

  // --- Compliance History ---

  const fetchComplianceHistory = useCallback(
    async (contactId: string) => {
      const history = await fieldOpsStore.getComplianceHistory(contactId);
      if (mounted.current) setComplianceHistory(history);
    },
    [],
  );

  // --- Export Reports ---

  const refreshExportReports = useCallback(async () => {
    const reports = await fieldOpsStore.getAllExportReports();
    if (mounted.current) setExportReports(reports);
  }, []);

  // --- Purge ---

  const purgeExpired = useCallback(async () => {
    const count = await fieldOpsStore.purgeExpired();
    await refreshMarketData();
    return count;
  }, [refreshMarketData]);

  return {
    marketSnapshot,
    fetchMarketSnapshot,
    allMarketSnapshots,
    refreshMarketData,
    propensityScore,
    fetchPropensityScore,
    hotLeads,
    refreshHotLeads,
    complianceHistory,
    fetchComplianceHistory,
    exportReports,
    refreshExportReports,
    isOnline,
    storageStats,
    purgeExpired,
  };
}

export default useFieldOpsOffline;
