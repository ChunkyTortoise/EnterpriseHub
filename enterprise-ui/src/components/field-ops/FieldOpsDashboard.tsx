'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, type Variants } from 'framer-motion';
import {
  ChartBarSquareIcon,
  FireIcon,
  ShieldCheckIcon,
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
  TrashIcon,
  ArrowPathIcon,
  SignalIcon,
  ChevronRightIcon,
  MapPinIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  BuildingOffice2Icon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  UserIcon,
} from '@heroicons/react/24/outline';
import { useFieldOpsOffline } from '@/hooks/useFieldOpsOffline';
import type {
  MarketSnapshot,
  PropensityScoreCache,
  ComplianceResultCache,
  ExportReportCache,
} from '@/lib/offline/FieldOpsOfflineStore';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RC_NEIGHBORHOODS = [
  'Victoria',
  'Haven',
  'Etiwanda',
  'Terra Vista',
  'Central Park',
] as const;

type TabId = 'market' | 'leads' | 'compliance' | 'reports';

interface TabDefinition {
  id: TabId;
  label: string;
  shortLabel: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

const TABS: TabDefinition[] = [
  { id: 'market', label: 'Market Snapshots', shortLabel: 'Market', icon: ChartBarSquareIcon },
  { id: 'leads', label: 'Hot Leads', shortLabel: 'Leads', icon: FireIcon },
  { id: 'compliance', label: 'Compliance', shortLabel: 'Comply', icon: ShieldCheckIcon },
  { id: 'reports', label: 'Export Reports', shortLabel: 'Reports', icon: DocumentArrowDownIcon },
];

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

function formatCurrency(value: number): string {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatTimestamp(ts: number): string {
  const date = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHr = Math.floor(diffMs / 3_600_000);

  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function temperatureColor(temp: string): string {
  switch (temp.toLowerCase()) {
    case 'hot':
      return 'text-red-400 bg-red-400/10 border-red-400/30';
    case 'warm':
      return 'text-amber-400 bg-amber-400/10 border-amber-400/30';
    case 'cold':
      return 'text-sky-400 bg-sky-400/10 border-sky-400/30';
    default:
      return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
  }
}

function riskColor(score: number): {
  text: string;
  bg: string;
  border: string;
  label: string;
} {
  if (score <= 30) {
    return {
      text: 'text-emerald-400',
      bg: 'bg-emerald-400/10',
      border: 'border-emerald-400/30',
      label: 'LOW',
    };
  }
  if (score <= 70) {
    return {
      text: 'text-amber-400',
      bg: 'bg-amber-400/10',
      border: 'border-amber-400/30',
      label: 'MED',
    };
  }
  return {
    text: 'text-red-400',
    bg: 'bg-red-400/10',
    border: 'border-red-400/30',
    label: 'HIGH',
  };
}

function conditionBadge(condition: string): string {
  switch (condition.toLowerCase()) {
    case "seller's market":
    case 'sellers market':
      return 'text-red-300 bg-red-500/15';
    case "buyer's market":
    case 'buyers market':
      return 'text-emerald-300 bg-emerald-500/15';
    case 'balanced':
      return 'text-sky-300 bg-sky-500/15';
    default:
      return 'text-gray-300 bg-gray-500/15';
  }
}

// ---------------------------------------------------------------------------
// Animation variants
// ---------------------------------------------------------------------------

const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.1 },
  },
};

const staggerItem: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
};

const tabContentVariant: Variants = {
  enter: { opacity: 0, x: 16 },
  center: { opacity: 1, x: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit: { opacity: 0, x: -16, transition: { duration: 0.15 } },
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Connection indicator in the header bar */
function ConnectionBadge({ isOnline }: { isOnline: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        <span
          className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
            isOnline ? 'bg-emerald-400 animate-ping' : 'bg-red-500'
          }`}
          style={isOnline ? { animationDuration: '2s' } : undefined}
        />
        <span
          className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
            isOnline ? 'bg-emerald-400' : 'bg-red-500'
          }`}
        />
      </span>
      <span
        className={`text-[11px] font-semibold tracking-wider uppercase ${
          isOnline ? 'text-emerald-400' : 'text-red-400'
        }`}
      >
        {isOnline ? 'Online' : 'Offline'}
      </span>
    </div>
  );
}

/** Neighborhood selector pills */
function NeighborhoodSelector({
  selected,
  onSelect,
}: {
  selected: string;
  onSelect: (n: string) => void;
}) {
  return (
    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide -mx-1 px-1">
      {RC_NEIGHBORHOODS.map((n) => {
        const active = n === selected;
        return (
          <button
            key={n}
            onClick={() => onSelect(n)}
            className={`
              flex-shrink-0 px-3 py-1.5 rounded-lg text-[11px] font-semibold tracking-wide
              uppercase transition-all duration-200 border
              ${
                active
                  ? 'bg-jorge-electric/20 border-jorge-electric/60 text-jorge-glow shadow-sm shadow-jorge-electric/20'
                  : 'bg-white/[0.03] border-white/[0.06] text-gray-500 hover:text-gray-300 hover:border-white/10 active:scale-95'
              }
            `}
          >
            {n}
          </button>
        );
      })}
    </div>
  );
}

/** Market snapshot data card */
function MarketCard({ snapshot }: { snapshot: MarketSnapshot }) {
  return (
    <motion.div
      variants={staggerItem}
      className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
    >
      {/* Card header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.04]">
        <div className="flex items-center gap-2">
          <MapPinIcon className="w-4 h-4 text-jorge-electric" />
          <span className="text-sm font-semibold text-gray-200 tracking-wide">
            {snapshot.neighborhood}
          </span>
        </div>
        <span className={`text-[10px] font-bold tracking-widest uppercase px-2 py-0.5 rounded-full ${conditionBadge(snapshot.market_condition)}`}>
          {snapshot.market_condition}
        </span>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-px bg-white/[0.03]">
        <MetricCell
          icon={CurrencyDollarIcon}
          label="Median Price"
          value={formatCurrency(snapshot.median_price)}
          accent="text-jorge-gold"
        />
        <MetricCell
          icon={ClockIcon}
          label="Days on Market"
          value={`${snapshot.avg_days_on_market}`}
          accent="text-jorge-glow"
        />
        <MetricCell
          icon={BuildingOffice2Icon}
          label="Active Inventory"
          value={`${snapshot.active_inventory}`}
          accent="text-jorge-electric"
        />
        <MetricCell
          icon={ArrowTrendingUpIcon}
          label="Appreciation"
          value={`${(snapshot.appreciation_rate * 100).toFixed(1)}%`}
          accent={snapshot.appreciation_rate >= 0 ? 'text-emerald-400' : 'text-red-400'}
        />
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-white/[0.04]">
        <span className="text-[10px] text-gray-600 font-mono">
          ${snapshot.avg_price_per_sqft.toFixed(0)}/sqft
        </span>
        <span className="text-[10px] text-gray-600">
          Competition: {(snapshot.buyer_competition_index * 10).toFixed(1)}/10
        </span>
        <span className="text-[10px] text-gray-600">
          {formatTimestamp(snapshot.timestamp)}
        </span>
      </div>
    </motion.div>
  );
}

/** A single metric cell inside the market card grid */
function MetricCell({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="px-4 py-3 bg-black/20">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className={`w-3.5 h-3.5 ${accent}`} />
        <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">
          {label}
        </span>
      </div>
      <span className={`text-lg font-bold tracking-tight ${accent}`}>{value}</span>
    </div>
  );
}

/** A single hot lead row */
function LeadRow({ lead }: { lead: PropensityScoreCache }) {
  const [expanded, setExpanded] = useState(false);
  const tempClass = temperatureColor(lead.temperature);

  return (
    <motion.div
      variants={staggerItem}
      className="border border-white/[0.06] rounded-xl bg-white/[0.02] overflow-hidden"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-4 py-3 flex items-center gap-3 active:bg-white/[0.03] transition-colors"
      >
        {/* Conversion probability ring */}
        <div className="relative flex-shrink-0">
          <svg className="w-11 h-11 -rotate-90" viewBox="0 0 44 44">
            <circle
              cx="22"
              cy="22"
              r="18"
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="3"
            />
            <circle
              cx="22"
              cy="22"
              r="18"
              fill="none"
              stroke={
                lead.conversion_probability >= 0.7
                  ? '#f87171'
                  : lead.conversion_probability >= 0.4
                  ? '#fbbf24'
                  : '#38bdf8'
              }
              strokeWidth="3"
              strokeDasharray={`${lead.conversion_probability * 113.1} 113.1`}
              strokeLinecap="round"
              className="transition-all duration-500"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-white">
            {(lead.conversion_probability * 100).toFixed(0)}
          </span>
        </div>

        {/* Lead info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <UserIcon className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-sm font-semibold text-gray-200 truncate">
              {lead.contact_id}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${tempClass}`}
            >
              {lead.temperature}
            </span>
            <span className="text-[10px] text-gray-500 truncate">
              {lead.predicted_timeline}
            </span>
          </div>
        </div>

        {/* Chevron */}
        <ChevronRightIcon
          className={`w-4 h-4 text-gray-600 transition-transform duration-200 flex-shrink-0 ${
            expanded ? 'rotate-90' : ''
          }`}
        />
      </button>

      {/* Expanded details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pt-1 border-t border-white/[0.04] space-y-3">
              {/* Recommended approach */}
              <div>
                <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium block mb-1">
                  Recommended Approach
                </span>
                <p className="text-xs text-gray-300 leading-relaxed">
                  {lead.recommended_approach}
                </p>
              </div>

              {/* Primary event */}
              {lead.primary_event && (
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium block mb-1">
                    Primary Event
                  </span>
                  <p className="text-xs text-jorge-glow">{lead.primary_event}</p>
                </div>
              )}

              {/* Confidence */}
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-gray-500 uppercase tracking-wider">
                  Confidence
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-jorge-electric rounded-full transition-all duration-500"
                      style={{ width: `${lead.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-gray-400">
                    {formatPercent(lead.confidence)}
                  </span>
                </div>
              </div>

              {/* Cached time */}
              <div className="text-[10px] text-gray-600 text-right">
                Cached {formatTimestamp(lead.timestamp)}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/** Compliance result row */
function ComplianceRow({ result }: { result: ComplianceResultCache }) {
  const [expanded, setExpanded] = useState(false);
  const risk = riskColor(result.risk_score);

  const statusIcon =
    result.status === 'pass' ? (
      <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
    ) : result.status === 'warning' ? (
      <ExclamationTriangleIcon className="w-4 h-4 text-amber-400" />
    ) : (
      <XCircleIcon className="w-4 h-4 text-red-400" />
    );

  return (
    <motion.div
      variants={staggerItem}
      className="border border-white/[0.06] rounded-xl bg-white/[0.02] overflow-hidden"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-4 py-3 flex items-center gap-3 active:bg-white/[0.03] transition-colors"
      >
        {statusIcon}
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-300 line-clamp-1">{result.message}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-gray-500">{result.contact_id}</span>
            <span className="text-[10px] text-gray-600">{formatTimestamp(result.timestamp)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${risk.text} ${risk.bg} ${risk.border}`}
          >
            {risk.label}
          </span>
          <span className={`text-xs font-mono font-bold ${risk.text}`}>
            {result.risk_score}
          </span>
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pt-1 border-t border-white/[0.04] space-y-2">
              {/* Violations */}
              {result.violations.length > 0 && (
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium block mb-1.5">
                    Violations ({result.violations.length})
                  </span>
                  <div className="space-y-1.5">
                    {result.violations.map((v, i) => (
                      <div
                        key={i}
                        className="text-xs bg-red-500/5 border border-red-500/10 rounded-lg px-3 py-2"
                      >
                        <span className="text-red-300 font-semibold">{v.category}:</span>{' '}
                        <span className="text-gray-400">{v.explanation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Safe alternative */}
              {result.safe_alternative && (
                <div>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium block mb-1">
                    Safe Alternative
                  </span>
                  <p className="text-xs text-emerald-300/80 leading-relaxed bg-emerald-500/5 border border-emerald-500/10 rounded-lg px-3 py-2">
                    {result.safe_alternative}
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/** Export report row */
function ReportRow({ report }: { report: ExportReportCache }) {
  const handleView = useCallback(() => {
    // Open content in a new window for viewing
    const blob = new Blob([report.content], {
      type: report.format === 'pdf' ? 'application/pdf' : 'text/plain',
    });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    // Revoke after a delay so the tab can load
    setTimeout(() => URL.revokeObjectURL(url), 30_000);
  }, [report]);

  const handleDownload = useCallback(() => {
    const blob = new Blob([report.content], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = report.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [report]);

  const typeColor = useMemo(() => {
    switch (report.report_type.toLowerCase()) {
      case 'cma':
        return 'text-jorge-gold bg-jorge-gold/10 border-jorge-gold/30';
      case 'market':
        return 'text-jorge-electric bg-jorge-electric/10 border-jorge-electric/30';
      case 'lead':
        return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30';
      default:
        return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
    }
  }, [report.report_type]);

  return (
    <motion.div
      variants={staggerItem}
      className="border border-white/[0.06] rounded-xl bg-white/[0.02] px-4 py-3"
    >
      <div className="flex items-center gap-3">
        <DocumentArrowDownIcon className="w-5 h-5 text-gray-500 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-200 font-medium truncate">{report.filename}</p>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${typeColor}`}
            >
              {report.report_type}
            </span>
            <span className="text-[10px] text-gray-600 uppercase">{report.format}</span>
            <span className="text-[10px] text-gray-600">{formatTimestamp(report.timestamp)}</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={handleView}
            className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-gray-400 hover:text-jorge-glow hover:border-jorge-glow/30 active:scale-90 transition-all"
            aria-label={`View ${report.filename}`}
          >
            <EyeIcon className="w-4 h-4" />
          </button>
          <button
            onClick={handleDownload}
            className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-gray-400 hover:text-jorge-electric hover:border-jorge-electric/30 active:scale-90 transition-all"
            aria-label={`Download ${report.filename}`}
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}

/** Empty state for any tab */
function EmptyState({ message, icon: Icon }: { message: string; icon: React.ComponentType<React.SVGProps<SVGSVGElement>> }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-4">
        <Icon className="w-6 h-6 text-gray-600" />
      </div>
      <p className="text-sm text-gray-500 max-w-[220px]">{message}</p>
    </div>
  );
}

/** Shimmer loading placeholder */
function LoadingShimmer({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-white/[0.04] bg-white/[0.02] p-4 animate-pulse"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-white/[0.05]" />
            <div className="flex-1 space-y-2">
              <div className="h-3 bg-white/[0.05] rounded w-3/4" />
              <div className="h-2 bg-white/[0.03] rounded w-1/2" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Dashboard Component
// ---------------------------------------------------------------------------

export function FieldOpsDashboard() {
  const {
    marketSnapshot,
    fetchMarketSnapshot,
    allMarketSnapshots,
    refreshMarketData,
    hotLeads,
    refreshHotLeads,
    complianceHistory,
    fetchComplianceHistory,
    exportReports,
    refreshExportReports,
    isOnline,
    storageStats,
    purgeExpired,
  } = useFieldOpsOffline();

  // -- Local state --
  const [activeTab, setActiveTab] = useState<TabId>('market');
  const [selectedNeighborhood, setSelectedNeighborhood] = useState<string>(RC_NEIGHBORHOODS[0]);
  const [complianceSearch, setComplianceSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isPurging, setIsPurging] = useState(false);
  const [purgeResult, setPurgeResult] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // -- Initial data load --
  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        await Promise.allSettled([
          refreshMarketData(),
          refreshHotLeads(),
          refreshExportReports(),
        ]);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [refreshMarketData, refreshHotLeads, refreshExportReports]);

  // -- Fetch market snapshot when neighborhood changes --
  useEffect(() => {
    fetchMarketSnapshot(selectedNeighborhood);
  }, [selectedNeighborhood, fetchMarketSnapshot]);

  // -- Refresh handler for current tab --
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      switch (activeTab) {
        case 'market':
          await fetchMarketSnapshot(selectedNeighborhood);
          await refreshMarketData();
          break;
        case 'leads':
          await refreshHotLeads();
          break;
        case 'compliance':
          if (complianceSearch.trim()) {
            await fetchComplianceHistory(complianceSearch.trim());
          }
          break;
        case 'reports':
          await refreshExportReports();
          break;
      }
    } finally {
      setRefreshing(false);
    }
  }, [
    activeTab,
    selectedNeighborhood,
    complianceSearch,
    fetchMarketSnapshot,
    refreshMarketData,
    refreshHotLeads,
    fetchComplianceHistory,
    refreshExportReports,
  ]);

  // -- Purge handler --
  const handlePurge = useCallback(async () => {
    setIsPurging(true);
    setPurgeResult(null);
    try {
      const count = await purgeExpired();
      setPurgeResult(count);
      // Clear result after 4 seconds
      setTimeout(() => setPurgeResult(null), 4000);
    } finally {
      setIsPurging(false);
    }
  }, [purgeExpired]);

  // -- Filtered compliance results --
  const filteredCompliance = useMemo(() => {
    if (!complianceSearch.trim()) return complianceHistory;
    const q = complianceSearch.toLowerCase();
    return complianceHistory.filter(
      (r) =>
        r.contact_id.toLowerCase().includes(q) ||
        r.message.toLowerCase().includes(q) ||
        r.status.toLowerCase().includes(q),
    );
  }, [complianceHistory, complianceSearch]);

  // -- Total cached items --
  const totalCached = useMemo(() => {
    if (!storageStats) return 0;
    return Object.values(storageStats).reduce((sum, n) => sum + n, 0);
  }, [storageStats]);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <div className="flex flex-col min-h-screen bg-[#080a0e]">
      {/* ================================================================ */}
      {/* HEADER BAR                                                       */}
      {/* ================================================================ */}
      <header className="sticky top-0 z-30 bg-[#0c0f14]/95 backdrop-blur-md border-b border-white/[0.06]">
        <div className="flex items-center justify-between px-4 py-3 max-w-2xl mx-auto">
          <div className="flex items-center gap-3">
            {/* Geometric brand mark */}
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-jorge-electric to-jorge-glow/60 flex items-center justify-center shadow-lg shadow-jorge-electric/20">
              <SignalIcon className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-100 tracking-wide uppercase">
                Field Operations
              </h1>
              <p className="text-[10px] text-gray-500 font-medium tracking-wider uppercase">
                Rancho Cucamonga
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ConnectionBadge isOnline={isOnline} />
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-gray-400 hover:text-jorge-glow hover:border-jorge-glow/20 active:scale-90 transition-all disabled:opacity-40"
              aria-label="Refresh data"
            >
              <ArrowPathIcon
                className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
              />
            </button>
          </div>
        </div>

        {/* ============================================================== */}
        {/* TAB BAR                                                        */}
        {/* ============================================================== */}
        <div className="max-w-2xl mx-auto px-4 pb-2">
          <nav className="flex gap-1" role="tablist">
            {TABS.map((tab) => {
              const active = tab.id === activeTab;
              const TabIcon = tab.icon;
              return (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex-1 flex flex-col items-center gap-1 py-2 px-1 rounded-lg
                    text-[10px] font-semibold tracking-wider uppercase
                    transition-all duration-200
                    ${
                      active
                        ? 'bg-jorge-electric/10 text-jorge-glow border border-jorge-electric/20'
                        : 'text-gray-600 border border-transparent hover:text-gray-400 active:scale-95'
                    }
                  `}
                >
                  <TabIcon className={`w-4 h-4 ${active ? 'text-jorge-electric' : ''}`} />
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.shortLabel}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* ================================================================ */}
      {/* TAB CONTENT                                                      */}
      {/* ================================================================ */}
      <main className="flex-1 px-4 py-4 max-w-2xl mx-auto w-full overflow-y-auto">
        <AnimatePresence mode="wait">
          {/* ---- MARKET TAB ---- */}
          {activeTab === 'market' && (
            <motion.div
              key="market"
              variants={tabContentVariant}
              initial="enter"
              animate="center"
              exit="exit"
              className="space-y-4"
            >
              <NeighborhoodSelector
                selected={selectedNeighborhood}
                onSelect={setSelectedNeighborhood}
              />

              {isLoading ? (
                <LoadingShimmer count={1} />
              ) : marketSnapshot ? (
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="show"
                >
                  <MarketCard snapshot={marketSnapshot} />
                </motion.div>
              ) : (
                <EmptyState
                  icon={ChartBarSquareIcon}
                  message="No cached data for this neighborhood. Tap refresh while online to fetch."
                />
              )}

              {/* All cached snapshots summary */}
              {allMarketSnapshots.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold px-1">
                    All Cached Neighborhoods ({allMarketSnapshots.length})
                  </h3>
                  <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="show"
                    className="grid gap-2"
                  >
                    {allMarketSnapshots
                      .filter((s) => s.neighborhood !== selectedNeighborhood)
                      .map((s) => (
                        <motion.button
                          key={s.neighborhood}
                          variants={staggerItem}
                          onClick={() => setSelectedNeighborhood(s.neighborhood)}
                          className="flex items-center justify-between px-4 py-3 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:border-white/[0.1] active:scale-[0.98] transition-all text-left"
                        >
                          <div className="flex items-center gap-2">
                            <MapPinIcon className="w-3.5 h-3.5 text-gray-600" />
                            <span className="text-sm text-gray-300 font-medium">
                              {s.neighborhood}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-jorge-gold font-bold">
                              {formatCurrency(s.median_price)}
                            </span>
                            <ChevronRightIcon className="w-3.5 h-3.5 text-gray-700" />
                          </div>
                        </motion.button>
                      ))}
                  </motion.div>
                </div>
              )}
            </motion.div>
          )}

          {/* ---- LEADS TAB ---- */}
          {activeTab === 'leads' && (
            <motion.div
              key="leads"
              variants={tabContentVariant}
              initial="enter"
              animate="center"
              exit="exit"
              className="space-y-3"
            >
              {/* Lead count header */}
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                  <FireIcon className="w-4 h-4 text-red-400" />
                  <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">
                    Hot Propensity Scores
                  </span>
                </div>
                <span className="text-[10px] text-gray-600 font-mono">
                  {hotLeads.length} result{hotLeads.length !== 1 ? 's' : ''}
                </span>
              </div>

              {isLoading ? (
                <LoadingShimmer count={4} />
              ) : hotLeads.length > 0 ? (
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="show"
                  className="space-y-2"
                >
                  {hotLeads.map((lead) => (
                    <LeadRow key={lead.contact_id} lead={lead} />
                  ))}
                </motion.div>
              ) : (
                <EmptyState
                  icon={FireIcon}
                  message="No hot leads cached. Scores sync automatically when online."
                />
              )}
            </motion.div>
          )}

          {/* ---- COMPLIANCE TAB ---- */}
          {activeTab === 'compliance' && (
            <motion.div
              key="compliance"
              variants={tabContentVariant}
              initial="enter"
              animate="center"
              exit="exit"
              className="space-y-3"
            >
              {/* Search bar */}
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                <input
                  type="text"
                  value={complianceSearch}
                  onChange={(e) => setComplianceSearch(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && complianceSearch.trim()) {
                      fetchComplianceHistory(complianceSearch.trim());
                    }
                  }}
                  placeholder="Search by contact ID..."
                  className="
                    w-full pl-9 pr-4 py-2.5 rounded-xl
                    bg-white/[0.03] border border-white/[0.08]
                    text-sm text-gray-200 placeholder:text-gray-600
                    focus:outline-none focus:border-jorge-electric/40 focus:bg-white/[0.05]
                    transition-all
                  "
                />
                {complianceSearch && (
                  <button
                    onClick={() => setComplianceSearch('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                    aria-label="Clear search"
                  >
                    <XCircleIcon className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Search hint */}
              {complianceHistory.length === 0 && !complianceSearch && (
                <div className="text-center py-8">
                  <ShieldCheckIcon className="w-8 h-8 text-gray-700 mx-auto mb-3" />
                  <p className="text-xs text-gray-500">
                    Enter a contact ID and press Enter to load compliance history
                  </p>
                </div>
              )}

              {/* Results */}
              {filteredCompliance.length > 0 ? (
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="show"
                  className="space-y-2"
                >
                  {filteredCompliance.map((result, i) => (
                    <ComplianceRow key={result.id ?? `${result.contact_id}-${i}`} result={result} />
                  ))}
                </motion.div>
              ) : complianceSearch && complianceHistory.length > 0 ? (
                <EmptyState
                  icon={MagnifyingGlassIcon}
                  message="No results match your search filter."
                />
              ) : null}
            </motion.div>
          )}

          {/* ---- REPORTS TAB ---- */}
          {activeTab === 'reports' && (
            <motion.div
              key="reports"
              variants={tabContentVariant}
              initial="enter"
              animate="center"
              exit="exit"
              className="space-y-3"
            >
              <div className="flex items-center justify-between px-1">
                <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">
                  Cached Reports
                </span>
                <span className="text-[10px] text-gray-600 font-mono">
                  {exportReports.length} file{exportReports.length !== 1 ? 's' : ''}
                </span>
              </div>

              {isLoading ? (
                <LoadingShimmer count={3} />
              ) : exportReports.length > 0 ? (
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="show"
                  className="space-y-2"
                >
                  {exportReports.map((report) => (
                    <ReportRow key={report.report_id} report={report} />
                  ))}
                </motion.div>
              ) : (
                <EmptyState
                  icon={DocumentArrowDownIcon}
                  message="No reports cached locally. Generate reports from the BI dashboard."
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* ================================================================ */}
      {/* FOOTER - Storage Stats                                           */}
      {/* ================================================================ */}
      <footer className="sticky bottom-0 z-30 bg-[#0c0f14]/95 backdrop-blur-md border-t border-white/[0.06]">
        <div className="max-w-2xl mx-auto px-4 py-3 space-y-2">
          {/* Storage counts */}
          {storageStats && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 flex-wrap">
                {Object.entries(storageStats).map(([key, count]) => {
                  // Convert camelCase key to shorter readable label
                  const labels: Record<string, string> = {
                    marketSnapshots: 'MKT',
                    propensityScores: 'LEADS',
                    complianceResults: 'CMPL',
                    forecasts: 'FCST',
                    exportReports: 'RPT',
                  };
                  return (
                    <div key={key} className="flex items-center gap-1">
                      <span className="text-[9px] text-gray-600 uppercase tracking-wider font-medium">
                        {labels[key] ?? key}
                      </span>
                      <span className="text-[10px] text-gray-400 font-mono font-bold">
                        {count}
                      </span>
                    </div>
                  );
                })}
              </div>

              <span className="text-[10px] text-gray-600 font-mono">
                {totalCached} total
              </span>
            </div>
          )}

          {/* Purge button row */}
          <div className="flex items-center justify-between">
            <AnimatePresence>
              {purgeResult !== null && (
                <motion.span
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-[10px] text-jorge-glow font-medium"
                >
                  {purgeResult === 0
                    ? 'Nothing to purge -- all data is fresh'
                    : `Purged ${purgeResult} expired item${purgeResult !== 1 ? 's' : ''}`}
                </motion.span>
              )}
            </AnimatePresence>

            <button
              onClick={handlePurge}
              disabled={isPurging}
              className="
                ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                bg-white/[0.03] border border-white/[0.08]
                text-[10px] font-semibold text-gray-500 uppercase tracking-wider
                hover:text-red-400 hover:border-red-400/20 hover:bg-red-400/5
                active:scale-95 transition-all disabled:opacity-40
              "
            >
              <TrashIcon className={`w-3.5 h-3.5 ${isPurging ? 'animate-pulse' : ''}`} />
              <span>{isPurging ? 'Purging...' : 'Purge Expired'}</span>
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default FieldOpsDashboard;
