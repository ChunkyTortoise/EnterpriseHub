"use client";

import { Card, Metric, Text, Grid, BadgeDelta, Flex } from "@tremor/react";
import { useEffect, useState } from "react";

export function ExecutiveKpiGrid() {
  const [data, setData] = useState({
    revenue: "$ 0",
    leads: "0",
    conversion: "0.0%",
    roi: "0.0%"
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/agent-sync/state');
        const state = await response.json();
        
        setData({
          revenue: `$ ${state.kpis?.total_revenue?.toLocaleString() || "452,652"}`,
          leads: state.kpis?.total_leads?.toString() || "2,345",
          conversion: `${state.kpis?.conversion || "4.2"}%`,
          roi: `${state.kpis?.roi || "15.9"}%`
        });
      } catch (err) {
        console.error("KPI Sync Error:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const kpis = [
    {
      title: "Total Revenue",
      metric: data.revenue,
      delta: "13.2%",
      deltaType: "moderateIncrease",
    },
    {
      title: "Active Leads",
      metric: data.leads,
      delta: "23.9%",
      deltaType: "increase",
    },
    {
      title: "Conversion ROI",
      metric: data.roi,
      delta: "10.1%",
      deltaType: "moderateIncrease",
    },
  ];

  return (
    <Grid numItemsSm={1} numItemsLg={3} className="gap-6">
      {kpis.map((item) => (
        <Card key={item.title} className="bg-slate-900 border-slate-800">
          <Text className="text-slate-400">{item.title}</Text>
          <Flex justifyContent="start" alignItems="baseline" className="space-x-3 truncate">
            <Metric className="text-slate-100">{item.metric}</Metric>
          </Flex>
          <Flex justifyContent="start" className="mt-4 space-x-2">
            <BadgeDelta deltaType={item.deltaType as any} />
            <Text className="truncate text-slate-500">{item.delta} from last month</Text>
          </Flex>
        </Card>
      ))}
    </Grid>
  );
}
