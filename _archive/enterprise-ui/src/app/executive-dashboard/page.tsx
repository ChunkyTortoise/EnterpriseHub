
import React from 'react';
import { ExecutiveKpiGrid } from '@/components/ExecutiveKpiGrid';
import { LeadVolumeChart } from '@/components/LeadVolumeChart';

export default function ExecutiveDashboardPage() {
  return (
    <div className="p-8 space-y-8 bg-slate-50 min-h-screen">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Executive Dashboard</h1>
        <p className="text-slate-500">Real-time performance metrics for your real estate empire.</p>
      </div>
      
      <ExecutiveKpiGrid />
      
      <div className="grid grid-cols-1 gap-6">
        <LeadVolumeChart />
      </div>
    </div>
  );
}
