
import { Card, Title, AreaChart } from "@tremor/react";

const chartdata = [
  { date: "Jan 22", "Leads": 2890, "Conversions": 2338 },
  { date: "Feb 22", "Leads": 2756, "Conversions": 2103 },
  { date: "Mar 22", "Leads": 3322, "Conversions": 2194 },
  { date: "Apr 22", "Leads": 3470, "Conversions": 2108 },
  { date: "May 22", "Leads": 3475, "Conversions": 1812 },
  { date: "Jun 22", "Leads": 3129, "Conversions": 1726 },
];

export function LeadVolumeChart() {
  return (
    <Card>
      <Title>Lead Volume & Conversions</Title>
      <AreaChart
        className="h-72 mt-4"
        data={chartdata}
        index="date"
        categories={["Leads", "Conversions"]}
        colors={["indigo", "cyan"]}
      />
    </Card>
  );
}
