'use client';

import Link from 'next/link';
import { CheckCircle, AlertTriangle, FileText, Database, Shield } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function ProofMetricsPage() {
  const dataSources = [
    {
      name: 'Agent Ecosystem Status',
      status: 'mixed',
      evidence: '/api/agents/statuses',
      note: 'Live cache if available, fallback to demo labels'
    },
    {
      name: 'Client Demo Sessions',
      status: 'sandbox-or-synthetic',
      evidence: '/api/v1/client-demonstrations/sessions',
      note: 'Sandbox DB preferred, synthetic fallback labeled'
    },
    {
      name: 'Business Intelligence Dashboard',
      status: 'api-or-synthetic',
      evidence: '/api/intelligence/executive-dashboard',
      note: 'API feed preferred, mock on failure with provenance'
    }
  ];

  const missingMetrics = [
    'p95/p99 API latency',
    'Error rate by endpoint',
    'Lead conversion uplift (baseline vs current)',
    'Response time SLA compliance',
    'Data sync lag (GHL ingestion)',
    'Active users / adoption'
  ];

  const validationArtifacts = [
    {
      label: 'Performance validation report',
      path: '/performance_validation_report.md'
    },
    {
      label: 'Security validation report',
      path: '/security_validation_report_20260120_050503.md'
    },
    {
      label: 'Deployment checklist',
      path: '/DEPLOYMENT_CHECKLIST.md'
    }
  ];

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Proof & Metrics</h1>
          <p className="text-gray-400">
            Evidence ledger for enterprise buyers. This page lists data sources, known gaps, and validation artifacts.
          </p>
        </div>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-400" />
              Data Sources
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {dataSources.map((source) => (
              <div key={source.name} className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <div className="font-semibold">{source.name}</div>
                  <div className="text-sm text-gray-400">Evidence: {source.evidence}</div>
                  <div className="text-xs text-gray-500 mt-1">{source.note}</div>
                </div>
                <Badge variant={source.status.includes('synthetic') ? 'destructive' : 'outline'}>
                  {source.status.replace(/-/g, ' ').toUpperCase()}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
                Missing Metrics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {missingMetrics.map((metric) => (
                <div key={metric} className="text-sm text-gray-300 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                  {metric}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-400" />
                Validation Artifacts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {validationArtifacts.map((artifact) => (
                <div key={artifact.label} className="flex items-center justify-between">
                  <div className="text-sm text-gray-300 flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    {artifact.label}
                  </div>
                  <Badge variant="outline">{artifact.path}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-purple-400" />
              Demo Integrity Notes
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-gray-300 space-y-2">
            <p>
              Any synthetic or fallback data is explicitly labeled in the UI. Sandbox data sources are preferred and marked
              when available. This ledger is the single source of truth for buyer-facing evidence.
            </p>
            <p>
              For walkthroughs, start at the{' '}
              <Link className="text-blue-400 underline" href="/presentation/demo">
                Client Demo Center
              </Link>{' '}
              and validate provenance badges before presenting ROI figures.
            </p>
            <p>
              Demo runbook: <span className="text-blue-400">/DEPLOYMENT_SETUP_GUIDE.md</span>
            </p>
            <div className="pt-4">
              <Button asChild className="bg-blue-600 hover:bg-blue-700">
                <a href="/api/evidence-pack">Download Evidence Pack</a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
