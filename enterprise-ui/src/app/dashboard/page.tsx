"use client";

import React from "react";
import { Card, Title, AreaChart, Metric, Text, Flex, BadgeDelta, Grid, ProgressBar, BarChart, Color } from "@tremor/react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LayoutDashboard, Users, MessageSquare, TrendingUp, Bell, RefreshCw, Mail, Phone, MapPin, BarChart3, Terminal as TerminalIcon, Settings2, ShieldAlert } from "lucide-react";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { applyDeltas, StateDelta } from "@/lib/ag-ui";
import { motion, AnimatePresence } from "framer-motion";
import { AgentConsole } from "@/components/AgentConsole";
import { makeAuthenticatedRequest } from "@/lib/api";
import { useRouter } from "next/navigation";
import { AgentRelationshipGraph } from "@/components/AgentRelationshipGraph";

const chartdata = [
  { date: "Jan 21", "Sales Bots": 2890, "Seller Bots": 2338 },
  { date: "Feb 21", "Sales Bots": 2756, "Seller Bots": 2103 },
  { date: "Mar 21", "Sales Bots": 3322, "Seller Bots": 2194 },
  { date: "Apr 21", "Sales Bots": 3470, "Seller Bots": 2108 },
  { date: "May 21", "Sales Bots": 3475, "Seller Bots": 1812 },
  { date: "Jun 21", "Sales Bots": 3129, "Seller Bots": 1726 },
];

export default function DashboardPage() {
  const [state, setState] = React.useState<any>(null);
  const [isSyncing, setIsSyncing] = React.useState(true);
  const router = useRouter();

  // Initial fetch
  React.useEffect(() => {
    const token = localStorage.getItem("enterprise_jwt_token");
    if (!token) {
      router.push("/login");
      return;
    }

    const fetchInitialState = async () => {
      try {                const data = await makeAuthenticatedRequest("/agent-sync/state");
                setState(data);        setIsSyncing(false);
      } catch (err) {
        console.error("Failed to sync with AI Agent Swarm:", err);
      }
    };

    fetchInitialState();

    // Polling for deltas every 2 seconds
    const interval = setInterval(async () => {
      try {
        const deltaResponse: StateDelta = await makeAuthenticatedRequest("/agent-sync/delta");
        
        if (deltaResponse.delta && deltaResponse.delta.length > 0) {
          setState((prev: any) => applyDeltas(prev, deltaResponse.delta));
        }
      } catch (err) {
        // Silent fail on polling for prototype
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  if (!state) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <Flex flexDirection="col" alignItems="center" className="space-y-4">
          <RefreshCw className="h-10 w-10 text-blue-600 animate-spin" />
          <Text className="text-xl font-medium">Synchronizing with Agent Swarm...</Text>
        </Flex>
      </div>
    );
  }

  // Map state to local variables for the render
  const kpis = [
    {
      title: "Total Active Leads",
      metric: state.kpis?.total_leads?.toLocaleString() || "0",
      progress: Math.round((state.kpis?.total_leads / 15000) * 100) || 0,
      target: "15,000",
      delta: "12.3%",
      deltaType: "moderateIncrease" as const,
    },
    {
      title: "AI Response Rate",
      metric: `${state.kpis?.response_rate}%` || "0%",
      progress: state.kpis?.response_rate || 0,
      target: "100%",
      delta: "0.5%",
      deltaType: "unchanged" as const,
    },
    {
      title: "Average Conversion",
      metric: `${state.kpis?.conversion}%` || "0%",
      progress: Math.round((state.kpis?.conversion / 40) * 100) || 0,
      target: "40%",
      delta: "4.1%",
      deltaType: "moderateIncrease" as const,
    },
  ];

  return (
    <main className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <Flex justifyContent="between" alignItems="center">
          <div>
            <Title className="text-3xl font-bold text-slate-900 flex items-center gap-2">
              Enterprise AI Dashboard
              {isSyncing ? <RefreshCw className="h-5 w-5 animate-spin text-blue-400" /> : <Badge className="bg-green-100 text-green-700 border-green-200">Live Sync</Badge>}
            </Title>
            <Text className="text-slate-500">Real-time performance metrics for Lyrio Agent Swarm</Text>
          </div>
          <div className="flex gap-4">
            <Button variant="outline" size="icon">
              <Bell className="h-4 w-4" />
            </Button>
            <Button 
              className="bg-red-600 hover:bg-red-700"
              onClick={() => {
                localStorage.removeItem("enterprise_jwt_token");
                router.push("/login");
              }}
            >
              Logout
            </Button>
            <Button
              className="bg-green-600 hover:bg-green-700"
              onClick={async () => {
                try {
                  const response = await makeAuthenticatedRequest("/reports/dashboard-summary", {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/pdf',
                    }
                  }, true) as Response; // Cast to Response type
                  
                  const blob = await response.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `dashboard_summary_${new Date().toISOString()}.pdf`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  window.URL.revokeObjectURL(url);
                } catch (error) {
                  console.error("Failed to generate report:", error);
                  alert("Failed to generate report. Please try again.");
                }
              }}
            >
              Generate Report
            </Button>
            <Button 
              className="bg-blue-600 hover:bg-blue-700"
              onClick={async () => {
                await makeAuthenticatedRequest("/agent-sync/thought?agent_id=Orchestrator&thought=Manual swarm trigger activated by Administrator.&status=Success", { method: 'POST' });
                // Briefly wait and simulate swarm steps
                setTimeout(() => makeAuthenticatedRequest("/agent-sync/thought?agent_id=SMSBot&thought=Sending priority SMS to high-value lead...", { method: 'POST' }), 1000);
                setTimeout(() => makeAuthenticatedRequest("/agent-sync/thought?agent_id=EmailBot&thought=Drafting personalized market narrative...", { method: 'POST' }), 2500);
              }}
            >
              Trigger Lead Swarm
            </Button>
          </div>
        </Flex>

        {/* KPI Grid */}
        <Grid numItemsMd={2} numItemsLg={3} className="gap-6">
          {kpis.map((item, idx) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              <Card decoration="top" decorationColor="blue">
                <Flex alignItems="start">
                  <div className="truncate">
                    <Text className="text-slate-500 font-medium">{item.title}</Text>
                    <Metric className="font-bold">{item.metric}</Metric>
                  </div>
                  <BadgeDelta deltaType={item.deltaType}>{item.delta}</BadgeDelta>
                </Flex>
                <Flex className="mt-4">
                  <Text className="truncate">{item.progress}% to target ({item.target})</Text>
                </Flex>
                <ProgressBar value={item.progress} color="blue" className="mt-2" />
              </Card>
            </motion.div>
          ))}
        </Grid>

        {/* Main Content Tabs */}
        <Tabs defaultValue="performance" className="w-full">
          <TabsList className="grid w-full grid-cols-6 max-w-3xl">
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="leads">Leads</TabsTrigger>
            <TabsTrigger value="market">Market</TabsTrigger>
            <TabsTrigger value="agents">Agents</TabsTrigger>
            <TabsTrigger value="console">Console</TabsTrigger>
            <TabsTrigger value="3d-swarm">3D Swarm</TabsTrigger>
          </TabsList>

          <TabsContent value="performance" className="mt-6 space-y-6">
            <Card>
              <Title>Bot Activity Over Time</Title>
              <Text>Comparison between Sales and Seller bot interactions</Text>
              <AreaChart
                className="h-72 mt-4"
                data={chartdata}
                index="date"
                categories={["Sales Bots", "Seller Bots"]}
                colors={["blue", "cyan"]}
                valueFormatter={(number: number) => `$ ${Intl.NumberFormat("us").format(number).toString()}`}
              />
            </Card>

            <Grid numItemsMd={2} className="gap-6">
              <Card>
                <Title>Top Markets</Title>
                <div className="mt-4 space-y-4">
                  {[
                    { market: "Austin, TX", share: "34%", color: "blue" },
                    { market: "Miami, FL", share: "28%", color: "cyan" },
                    { market: "Denver, CO", share: "22%", color: "indigo" },
                  ].map((item) => (
                    <div key={item.market} className="space-y-1">
                      <Flex>
                        <Text>{item.market}</Text>
                        <Text className="font-bold">{item.share}</Text>
                      </Flex>
                      <ProgressBar value={parseInt(item.share)} color={item.color as Color} />
                    </div>
                  ))}
                </div>
              </Card>

              <Card>
                <Title>Recent Agent Thoughts</Title>
                <div className="mt-4 space-y-4">
                  <AnimatePresence initial={false}>
                    {(state.recent_thoughts || []).length > 0 ? (
                      state.recent_thoughts.map((thought: any, idx: number) => (
                        <motion.div 
                          key={thought.timestamp + idx}
                          initial={{ opacity: 0, x: 20, height: 0 }}
                          animate={{ opacity: 1, x: 0, height: "auto" }}
                          exit={{ opacity: 0, x: -20, height: 0 }}
                          transition={{ duration: 0.3 }}
                          className="overflow-hidden"
                        >
                          <div className="flex items-start gap-4 p-3 rounded-lg border border-slate-100 bg-slate-50 mb-4">
                            <div className={`mt-1 h-2 w-2 rounded-full ${thought.status === "Critical" ? "bg-red-500" : thought.status === "Warning" ? "bg-amber-500" : "bg-green-500"}`} />
                            <div className="flex-1">
                              <Flex justifyContent="between">
                                <Text className="font-bold text-slate-900">{thought.agent}</Text>
                                <Text className="text-xs text-slate-400">{new Date(thought.timestamp).toLocaleTimeString()}</Text>
                              </Flex>
                              <Text className="text-sm">{thought.task}</Text>
                            </div>
                          </div>
                        </motion.div>
                      ))
                    ) : (
                      <div className="h-32 flex items-center justify-center border border-dashed rounded-lg">
                        <Text className="italic text-slate-400">Waiting for agent activity...</Text>
                      </div>
                    )}
                  </AnimatePresence>
                </div>
              </Card>
            </Grid>
          </TabsContent>

          <TabsContent value="leads">
            <Card>
              <Title>Lead Intelligence Hub</Title>
              <Text className="mt-2">Real-time ML-scored leads synchronized across your agent swarm.</Text>
              
              <Table className="mt-6">
                <TableHeader>
                  <TableRow>
                    <TableHead>Lead Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>AI Score</TableHead>
                    <TableHead>Market</TableHead>
                    <TableHead>Last Action</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(state.leads || []).map((lead: any) => (
                    <TableRow key={lead.id}>
                      <TableCell className="font-medium">{lead.name}</TableCell>
                      <TableCell>
                        <Badge className={
                          lead.status === "Hot" ? "bg-red-100 text-red-700 border-red-200" :
                          lead.status === "Warm" ? "bg-amber-100 text-amber-700 border-amber-200" :
                          "bg-slate-100 text-slate-700 border-slate-200"
                        }>
                          {lead.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Text>{lead.score}%</Text>
                          <ProgressBar value={lead.score} color={lead.score > 80 ? "red" : lead.score > 50 ? "amber" : "slate"} className="w-16" />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-slate-500">
                          <MapPin className="h-3 w-3" />
                          {lead.market}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500">{lead.last_action}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm">Details</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>

          <TabsContent value="market" className="mt-6 space-y-6">
            <Grid numItemsMd={2} className="gap-6">
              <Card>
                <Title>Market Appreciation Forecast</Title>
                <Text>AI-predicted price growth for next 12 months</Text>
                <BarChart
                  className="mt-6 h-64"
                  data={state.market_predictions || []}
                  index="neighborhood"
                  categories={["prediction"]}
                  colors={["blue"]}
                  valueFormatter={(number: any) => `${number}%`}
                  yAxisWidth={48}
                />
              </Card>

              <Card>
                <Title>Neighborhood Intelligence</Title>
                <Text>Real-time insights from MarketBot</Text>
                <div className="mt-6 space-y-4">
                  {(state.market_predictions || []).map((item: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-xl border border-slate-100 bg-slate-50 flex items-center justify-between">
                      <div>
                        <Text className="font-bold text-slate-900">{item.neighborhood}</Text>
                        <Text className="text-xs text-slate-500">Confidence: {item.confidence}</Text>
                      </div>
                      <div className="text-right">
                        <Badge className="bg-blue-100 text-blue-700 border-blue-200">
                          {item.prediction}
                        </Badge>
                        <Text className="text-xs text-slate-400 mt-1">{item.horizon}</Text>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </Grid>
          </TabsContent>

          <TabsContent value="console" className="mt-6">
            <AgentConsole />
          </TabsContent>

          <TabsContent value="agents">
            <Card>
              <Title>Swarm Management</Title>
              <Text className="mt-2">Configure and monitor your AI agent swarm health.</Text>
              
              <Grid numItemsMd={2} numItemsLg={4} className="gap-6 mt-6">
                {Object.entries(state.agents || {}).map(([name, data]: [string, any], idx) => (
                  <motion.div
                    key={name}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.05 }}
                  >
                    <Card className="p-4 border-slate-100 h-full">
                      <Flex justifyContent="between" alignItems="start">
                        <div className="space-y-1">
                          <Text className="font-bold text-slate-900">{name}</Text>
                          <Badge className={
                            data.status === "Active" ? "bg-green-100 text-green-700 border-green-200" :
                            data.status === "Maintenance" ? "bg-amber-100 text-amber-700 border-amber-200" :
                            "bg-slate-100 text-slate-700 border-slate-200"
                          }>
                            {data.status}
                          </Badge>
                        </div>
                        <div className="text-right">
                          <Text className="text-xs text-slate-400">Health</Text>
                          <Text className={`font-bold ${data.health > 90 ? "text-green-600" : data.health > 50 ? "text-amber-600" : "text-red-600"}`}>
                            {data.health}%
                          </Text>
                        </div>
                      </Flex>
                      
                      <div className="mt-6 space-y-2">
                        <Flex>
                          <Text className="text-xs">Uptime</Text>
                          <Text className="text-xs font-medium">{data.uptime}</Text>
                        </Flex>
                        <Flex>
                          <Text className="text-xs">Load</Text>
                          <Text className="text-xs font-medium">{data.load}</Text>
                        </Flex>
                        <ProgressBar value={data.health} color={data.health > 90 ? "green" : data.health > 50 ? "amber" : "red"} className="mt-2" />
                      </div>
                      
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" className="w-full mt-4 text-xs h-8">Configure</Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[425px]">
                          <DialogHeader>
                            <DialogTitle className="flex items-center gap-2">
                              <Settings2 className="h-5 w-5 text-blue-600" />
                              Configure {name}
                            </DialogTitle>
                            <DialogDescription>
                              Adjust swarm parameters and personality for this agent.
                            </DialogDescription>
                          </DialogHeader>
                          <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                              <Label htmlFor="personality" className="text-right">Personality</Label>
                              <Input id="personality" defaultValue="Professional" className="col-span-3" />
                            </div>
                            <div className="flex items-center justify-between space-x-2 border p-3 rounded-lg bg-slate-50">
                              <div className="flex flex-col space-y-1">
                                <Label className="text-sm font-bold flex items-center gap-2">
                                  <ShieldAlert className="h-4 w-4 text-amber-500" />
                                  Confrontational Mode
                                </Label>
                                <span className="text-[10px] text-slate-500 italic">Increases urgency for unresponsive leads.</span>
                              </div>
                              <Switch id="confrontational" />
                            </div>
                          </div>
                          <DialogFooter>
                            <Button type="submit" className="bg-blue-600 hover:bg-blue-700" onClick={async () => {
                               await makeAuthenticatedRequest(`/agent-sync/thought?agent_id=${name}&thought=Reconfigured by Administrator. Updating sub-routines.&status=Warning`, { method: 'POST' });
                            }}>
                              Save Configuration
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </Card>
                  </motion.div>
                ))}
              </Grid>
            </Card>
          </TabsContent>

          <TabsContent value="3d-swarm" className="mt-6">
            <Card className="h-[600px]">
                <Title>3D Agent Swarm Visualization</Title>
                <Text>Interactive 3D graph of agent relationships and activities.</Text>
                <div className="h-[500px] mt-4">
                    <AgentRelationshipGraph />
                </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
