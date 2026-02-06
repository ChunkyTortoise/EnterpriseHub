/**
 * Compliance & Security Dashboard - Jorge's Fort Knox Interface
 * Comprehensive monitoring of compliance status, security events, and audit trails
 */

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Shield,
  Lock,
  Eye,
  FileText,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  Database,
  Activity,
  TrendingUp,
  TrendingDown,
  Globe,
  Gavel,
  BookOpen,
  Award,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';

interface DashboardProps {
  className?: string;
  refreshInterval?: number;
}

interface ComplianceMetric {
  regulation: string;
  score: number;
  status: 'compliant' | 'warning' | 'violation' | 'critical';
  lastAudit: string;
  nextDue: string;
  violations: number;
}

interface SecurityEvent {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  description: string;
  status: 'open' | 'investigating' | 'resolved';
  affectedSystems: string[];
}

interface AuditRecord {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  result: 'success' | 'failure' | 'partial';
  severity: 'informational' | 'low' | 'medium' | 'high' | 'critical';
  complianceTags: string[];
}

const ComplianceSecurityDashboard: React.FC<DashboardProps> = ({
  className = '',
  refreshInterval = 300000 // 5 minutes
}) => {
  // Dashboard state
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Compliance data state
  const [complianceMetrics, setComplianceMetrics] = useState<ComplianceMetric[]>([]);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [auditRecords, setAuditRecords] = useState<AuditRecord[]>([]);

  // Real-time monitoring state
  const [isConnected, setIsConnected] = useState(true);
  const [alertsCount, setAlertsCount] = useState(0);

  // Mock data for demonstration (replace with real API calls)
  const mockComplianceData: ComplianceMetric[] = [
    { regulation: 'RESPA', score: 98.5, status: 'compliant', lastAudit: '2024-01-15', nextDue: '2024-04-15', violations: 0 },
    { regulation: 'Fair Housing', score: 96.8, status: 'compliant', lastAudit: '2024-01-10', nextDue: '2024-04-10', violations: 0 },
    { regulation: 'GDPR', score: 94.2, status: 'warning', lastAudit: '2024-01-20', nextDue: '2024-07-20', violations: 2 },
    { regulation: 'CCPA', score: 97.1, status: 'compliant', lastAudit: '2024-01-12', nextDue: '2024-07-12', violations: 1 },
    { regulation: 'State Licensing', score: 99.2, status: 'compliant', lastAudit: '2024-01-08', nextDue: '2024-04-08', violations: 0 },
    { regulation: 'MLS Rules', score: 95.7, status: 'warning', lastAudit: '2024-01-18', nextDue: '2024-04-18', violations: 3 }
  ];

  const mockSecurityEvents: SecurityEvent[] = [
    {
      id: 'evt_001',
      type: 'Failed Login Attempt',
      severity: 'medium',
      timestamp: '2024-01-24T10:30:00Z',
      description: 'Multiple failed login attempts from IP 192.168.1.100',
      status: 'investigating',
      affectedSystems: ['Auth Service']
    },
    {
      id: 'evt_002',
      type: 'Data Access',
      severity: 'low',
      timestamp: '2024-01-24T09:15:00Z',
      description: 'Bulk client data export performed',
      status: 'resolved',
      affectedSystems: ['Client Database']
    },
    {
      id: 'evt_003',
      type: 'Permission Change',
      severity: 'high',
      timestamp: '2024-01-24T08:45:00Z',
      description: 'Administrative permissions modified for user john.doe',
      status: 'resolved',
      affectedSystems: ['User Management']
    }
  ];

  const mockAuditRecords: AuditRecord[] = [
    {
      id: 'audit_001',
      timestamp: '2024-01-24T11:00:00Z',
      user: 'jorge.martinez',
      action: 'client_data_access',
      resource: 'client_profile_12345',
      result: 'success',
      severity: 'informational',
      complianceTags: ['data_protection', 'privacy']
    },
    {
      id: 'audit_002',
      timestamp: '2024-01-24T10:45:00Z',
      user: 'sarah.johnson',
      action: 'document_modification',
      resource: 'compliance_policy_v2.1',
      result: 'success',
      severity: 'medium',
      complianceTags: ['document_control', 'policy_management']
    }
  ];

  // Security trends data
  const securityTrends = [
    { month: 'Oct', events: 12, resolved: 11, critical: 1 },
    { month: 'Nov', events: 8, resolved: 8, critical: 0 },
    { month: 'Dec', events: 15, resolved: 14, critical: 2 },
    { month: 'Jan', events: 6, resolved: 5, critical: 0 }
  ];

  // Compliance trends data
  const complianceTrends = [
    { regulation: 'RESPA', q1: 97.2, q2: 98.1, q3: 98.5, q4: 98.5 },
    { regulation: 'Fair Housing', q1: 95.8, q2: 96.2, q3: 96.5, q4: 96.8 },
    { regulation: 'GDPR', q1: 92.1, q2: 93.5, q3: 94.0, q4: 94.2 },
    { regulation: 'CCPA', q1: 96.5, q2: 96.8, q3: 97.0, q4: 97.1 }
  ];

  // Load dashboard data
  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // Simulate API calls
      await new Promise(resolve => setTimeout(resolve, 1000));

      setComplianceMetrics(mockComplianceData);
      setSecurityEvents(mockSecurityEvents);
      setAuditRecords(mockAuditRecords);

      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-refresh dashboard
  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    const totalCompliance = complianceMetrics.reduce((sum, metric) => sum + metric.score, 0) / complianceMetrics.length;
    const criticalEvents = securityEvents.filter(event => event.severity === 'critical').length;
    const openEvents = securityEvents.filter(event => event.status === 'open').length;
    const totalViolations = complianceMetrics.reduce((sum, metric) => sum + metric.violations, 0);

    return {
      totalCompliance: totalCompliance || 0,
      criticalEvents,
      openEvents,
      totalViolations
    };
  }, [complianceMetrics, securityEvents]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'warning': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'violation': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white flex items-center gap-3">
            <Shield className="h-8 w-8 text-green-400" />
            Jorge's Fort Knox
          </h2>
          <p className="text-gray-400 mt-1">Enterprise Compliance & Security Command Center</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? 'Live Monitoring' : 'Offline'}
            </span>
          </div>

          <div className="text-sm text-gray-400">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </div>

          <Button onClick={loadDashboardData} disabled={isLoading} variant="outline">
            {isLoading ? 'Updating...' : 'Refresh'}
          </Button>
        </div>
      </div>

      {/* Alert Banner for Critical Issues */}
      {summaryMetrics.criticalEvents > 0 && (
        <Alert className="border-red-500/30 bg-red-500/10">
          <AlertTriangle className="h-4 w-4 text-red-400" />
          <AlertTitle className="text-red-400">Critical Security Alert</AlertTitle>
          <AlertDescription className="text-red-300">
            {summaryMetrics.criticalEvents} critical security events require immediate attention.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Overall Compliance</p>
                  <p className="text-2xl font-bold text-green-400">
                    {summaryMetrics.totalCompliance.toFixed(1)}%
                  </p>
                </div>
                <Award className="h-8 w-8 text-green-400" />
              </div>
              <Progress value={summaryMetrics.totalCompliance} className="mt-4" />
              <div className="mt-2 flex items-center text-sm">
                <CheckCircle className="h-4 w-4 text-green-400 mr-1" />
                <span className="text-green-400">Excellent Standing</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Security Events</p>
                  <p className="text-2xl font-bold text-blue-400">
                    {securityEvents.length}
                  </p>
                </div>
                <Shield className="h-8 w-8 text-blue-400" />
              </div>
              <div className="mt-2 flex items-center text-sm">
                <div className="flex items-center gap-4">
                  <span className="text-red-400">{summaryMetrics.criticalEvents} Critical</span>
                  <span className="text-yellow-400">{summaryMetrics.openEvents} Open</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Active Violations</p>
                  <p className="text-2xl font-bold text-orange-400">
                    {summaryMetrics.totalViolations}
                  </p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-400" />
              </div>
              <div className="mt-2 flex items-center text-sm">
                {summaryMetrics.totalViolations === 0 ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-400 mr-1" />
                    <span className="text-green-400">No Active Violations</span>
                  </>
                ) : (
                  <>
                    <Clock className="h-4 w-4 text-orange-400 mr-1" />
                    <span className="text-orange-400">Remediation in Progress</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Audit Records</p>
                  <p className="text-2xl font-bold text-purple-400">
                    {auditRecords.length.toLocaleString()}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-purple-400" />
              </div>
              <div className="mt-2 flex items-center text-sm">
                <Activity className="h-4 w-4 text-purple-400 mr-1" />
                <span className="text-purple-400">24/7 Monitoring</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-gray-800 border-gray-700">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="compliance" className="flex items-center gap-2">
            <Gavel className="h-4 w-4" />
            Compliance
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Audit Trail
          </TabsTrigger>
          <TabsTrigger value="privacy" className="flex items-center gap-2">
            <Lock className="h-4 w-4" />
            Privacy
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Compliance Radar Chart */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Award className="h-5 w-5" />
                  Compliance Health Check
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={complianceMetrics.map(metric => ({
                    regulation: metric.regulation,
                    score: metric.score,
                    fullMark: 100
                  }))}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="regulation" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      tick={{ fill: '#9CA3AF', fontSize: 10 }}
                    />
                    <Radar
                      name="Compliance Score"
                      dataKey="score"
                      stroke="#10B981"
                      fill="#10B981"
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Security Event Trends */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Security Event Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={securityTrends}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="month" tick={{ fill: '#9CA3AF' }} />
                    <YAxis tick={{ fill: '#9CA3AF' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px'
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="events"
                      stackId="1"
                      stroke="#3B82F6"
                      fill="#3B82F6"
                      fillOpacity={0.3}
                      name="Total Events"
                    />
                    <Area
                      type="monotone"
                      dataKey="critical"
                      stackId="2"
                      stroke="#EF4444"
                      fill="#EF4444"
                      fillOpacity={0.6}
                      name="Critical Events"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Real-time Activity Feed */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Real-time Security & Compliance Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {[...securityEvents, ...auditRecords.slice(0, 5)].map((event, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg border border-gray-600"
                  >
                    <div className="flex items-center gap-3">
                      {'type' in event ? (
                        <Shield className="h-5 w-5 text-blue-400" />
                      ) : (
                        <FileText className="h-5 w-5 text-purple-400" />
                      )}
                      <div>
                        <p className="text-white font-medium">
                          {'type' in event ? event.type : event.action}
                        </p>
                        <p className="text-sm text-gray-400">
                          {'description' in event ? event.description : event.resource}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={getSeverityColor('severity' in event ? event.severity : 'low')}
                      >
                        {'severity' in event ? event.severity : 'audit'}
                      </Badge>
                      <span className="text-sm text-gray-400">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Compliance Tab */}
        <TabsContent value="compliance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {complianceMetrics.map((metric, index) => (
              <motion.div
                key={metric.regulation}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center justify-between">
                      <span>{metric.regulation}</span>
                      <Badge className={getStatusColor(metric.status)}>
                        {metric.status}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-400">Compliance Score</span>
                        <span className="text-white font-bold">{metric.score.toFixed(1)}%</span>
                      </div>
                      <Progress value={metric.score} className="h-2" />
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Last Audit</span>
                        <span className="text-white">{metric.lastAudit}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Next Due</span>
                        <span className="text-white">{metric.nextDue}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Active Violations</span>
                        <span className={`font-medium ${metric.violations === 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {metric.violations}
                        </span>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-gray-700">
                      <Button variant="outline" size="sm" className="w-full">
                        View Details
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Compliance Trends Chart */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Compliance Trends Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={complianceTrends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="regulation" tick={{ fill: '#9CA3AF' }} />
                  <YAxis domain={[90, 100]} tick={{ fill: '#9CA3AF' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="q1" stroke="#3B82F6" strokeWidth={2} name="Q1" />
                  <Line type="monotone" dataKey="q2" stroke="#10B981" strokeWidth={2} name="Q2" />
                  <Line type="monotone" dataKey="q3" stroke="#F59E0B" strokeWidth={2} name="Q3" />
                  <Line type="monotone" dataKey="q4" stroke="#8B5CF6" strokeWidth={2} name="Q4" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <div className="space-y-4">
            {securityEvents.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${
                          event.severity === 'critical' ? 'bg-red-400' :
                          event.severity === 'high' ? 'bg-orange-400' :
                          event.severity === 'medium' ? 'bg-yellow-400' : 'bg-blue-400'
                        }`} />
                        <h3 className="text-white font-semibold">{event.type}</h3>
                        <Badge className={getSeverityColor(event.severity)}>
                          {event.severity}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={event.status === 'resolved' ? 'success' : 'warning'}>
                          {event.status}
                        </Badge>
                        <span className="text-sm text-gray-400">
                          {new Date(event.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>

                    <p className="text-gray-300 mb-4">{event.description}</p>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-400">Affected Systems:</span>
                        {event.affectedSystems.map(system => (
                          <Badge key={system} variant="outline" className="text-xs">
                            {system}
                          </Badge>
                        ))}
                      </div>
                      <Button variant="outline" size="sm">
                        Investigate
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Audit Trail Tab */}
        <TabsContent value="audit" className="space-y-6">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Recent Audit Records</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {auditRecords.map((record, index) => (
                  <motion.div
                    key={record.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg border border-gray-600"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-2 h-2 rounded-full ${
                        record.result === 'success' ? 'bg-green-400' :
                        record.result === 'failure' ? 'bg-red-400' : 'bg-yellow-400'
                      }`} />
                      <div>
                        <p className="text-white font-medium">{record.action}</p>
                        <p className="text-sm text-gray-400">{record.resource}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-400">{record.user}</span>
                      <div className="flex gap-1">
                        {record.complianceTags.map(tag => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <span className="text-sm text-gray-400">
                        {new Date(record.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacy Tab */}
        <TabsContent value="privacy" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  Global Privacy Compliance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">GDPR (Europe)</span>
                    <div className="flex items-center gap-2">
                      <Progress value={94.2} className="w-20" />
                      <span className="text-green-400 text-sm">94.2%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">CCPA (California)</span>
                    <div className="flex items-center gap-2">
                      <Progress value={97.1} className="w-20" />
                      <span className="text-green-400 text-sm">97.1%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">PIPEDA (Canada)</span>
                    <div className="flex items-center gap-2">
                      <Progress value={96.5} className="w-20" />
                      <span className="text-green-400 text-sm">96.5%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Data Subject Rights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-400">24</p>
                    <p className="text-sm text-gray-400">Access Requests</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-400">3</p>
                    <p className="text-sm text-gray-400">Deletion Requests</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-400">12</p>
                    <p className="text-sm text-gray-400">Consent Updates</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-400">1</p>
                    <p className="text-sm text-gray-400">Portability Requests</p>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-700">
                  <p className="text-sm text-gray-400">Average Response Time</p>
                  <p className="text-lg font-semibold text-green-400">18.5 hours</p>
                  <p className="text-xs text-gray-500">Well under 30-day requirement</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ComplianceSecurityDashboard;