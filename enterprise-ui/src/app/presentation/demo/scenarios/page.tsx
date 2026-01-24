// Jorge's Demo Scenario Selection & Configuration
// Professional scenario customization for client demonstrations

'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  PlayCircle,
  Settings,
  ArrowLeft,
  Clock,
  Users,
  Target,
  Brain,
  BarChart3,
  Monitor,
  Edit3,
  Save,
  RotateCcw,
  Download,
  Share2,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { motion } from 'framer-motion';
import useDemoMode, { useScenarioSelection } from '@/hooks/useDemoMode';
import { DemoScenarioSelector } from '@/components/demo/DemoScenarioSelector';
import { SyntheticDataViewer } from '@/components/demo/SyntheticDataViewer';
import { DemoControlPanel } from '@/components/demo/DemoControlPanel';

export default function ScenariosPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedScenarioId = searchParams.get('id');

  const [demoState, demoActions] = useDemoMode();
  const { scenarios, categorized } = useScenarioSelection();
  const [activeTab, setActiveTab] = useState('selection');
  const [customSettings, setCustomSettings] = useState({
    duration: 10,
    difficulty: 'intermediate',
    clientType: 'motivated_seller',
    propertyType: 'luxury_condo',
    marketCondition: 'hot_market',
    botPersonality: 'confrontational'
  });

  useEffect(() => {
    if (selectedScenarioId) {
      const scenario = scenarios.find(s => s.id === selectedScenarioId);
      if (scenario) {
        demoActions.loadScenario(selectedScenarioId);
        setActiveTab('configuration');
      }
    }
  }, [selectedScenarioId, scenarios, demoActions]);

  const handleScenarioSelect = async (scenarioId: string) => {
    await demoActions.loadScenario(scenarioId);
    setActiveTab('configuration');

    // Update URL
    const newParams = new URLSearchParams(searchParams);
    newParams.set('id', scenarioId);
    router.push(`/presentation/demo/scenarios?${newParams.toString()}`);
  };

  const handleStartDemo = () => {
    demoActions.enterPresentationMode();
    router.push('/presentation/demo/live');
  };

  const handleResetConfiguration = () => {
    setCustomSettings({
      duration: 10,
      difficulty: 'intermediate',
      clientType: 'motivated_seller',
      propertyType: 'luxury_condo',
      marketCondition: 'hot_market',
      botPersonality: 'confrontational'
    });
    demoActions.resetDemo();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/presentation/demo')}
                className="text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Demo Center
              </Button>

              <div className="flex items-center gap-2">
                <Settings className="w-6 h-6 text-blue-400" />
                <div>
                  <h1 className="text-xl font-bold text-white">Scenario Configuration</h1>
                  <p className="text-blue-200 text-sm">Customize demonstration parameters</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {demoState.currentScenario && (
                <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-400">
                  <Target className="w-4 h-4 mr-1" />
                  {demoState.currentScenario.name}
                </Badge>
              )}

              <Button
                onClick={handleStartDemo}
                disabled={!demoState.currentScenario}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                <PlayCircle className="w-4 h-4 mr-2" />
                Start Demo
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-white/5 border border-white/10">
            <TabsTrigger value="selection" className="data-[state=active]:bg-white/10">
              <Target className="w-4 h-4 mr-2" />
              Scenario Selection
            </TabsTrigger>
            <TabsTrigger
              value="configuration"
              disabled={!demoState.currentScenario}
              className="data-[state=active]:bg-blue-500/20"
            >
              <Settings className="w-4 h-4 mr-2" />
              Configuration
            </TabsTrigger>
            <TabsTrigger
              value="data"
              disabled={!demoState.currentScenario}
              className="data-[state=active]:bg-green-500/20"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Demo Data
            </TabsTrigger>
            <TabsTrigger
              value="preview"
              disabled={!demoState.currentScenario}
              className="data-[state=active]:bg-purple-500/20"
            >
              <Monitor className="w-4 h-4 mr-2" />
              Preview
            </TabsTrigger>
          </TabsList>

          {/* Scenario Selection Tab */}
          <TabsContent value="selection" className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Card className="bg-white/5 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    Choose Your Demo Scenario
                  </CardTitle>
                  <p className="text-gray-300">
                    Select a scenario that best demonstrates Jorge's AI capabilities for your client presentation
                  </p>
                </CardHeader>
                <CardContent>
                  <DemoScenarioSelector
                    scenarios={scenarios}
                    categorized={categorized}
                    selectedScenario={demoState.currentScenario}
                    onScenarioSelect={handleScenarioSelect}
                    isLoading={demoState.isLoading}
                  />
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* Configuration Tab */}
          <TabsContent value="configuration" className="space-y-6">
            {demoState.currentScenario && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-6"
              >
                {/* Scenario Overview */}
                <Card className="lg:col-span-2 bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center">
                      <Edit3 className="w-5 h-5 mr-2" />
                      Scenario Configuration
                    </CardTitle>
                    <p className="text-gray-300">
                      Customize demonstration parameters for optimal client engagement
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Demo Duration */}
                    <div className="space-y-3">
                      <Label className="text-white font-medium">Demo Duration</Label>
                      <div className="space-y-2">
                        <Slider
                          value={[customSettings.duration]}
                          onValueChange={(value) => setCustomSettings(prev => ({ ...prev, duration: value[0] }))}
                          max={30}
                          min={3}
                          step={1}
                          className="w-full"
                        />
                        <div className="flex justify-between text-sm text-gray-400">
                          <span>3 min (Quick)</span>
                          <span className="text-blue-400">{customSettings.duration} minutes</span>
                          <span>30 min (Comprehensive)</span>
                        </div>
                      </div>
                    </div>

                    {/* Client Type */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-white font-medium">Client Profile</Label>
                        <Select
                          value={customSettings.clientType}
                          onValueChange={(value) => setCustomSettings(prev => ({ ...prev, clientType: value }))}
                        >
                          <SelectTrigger className="bg-white/5 border-white/20 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20">
                            <SelectItem value="motivated_seller">Motivated Seller</SelectItem>
                            <SelectItem value="first_time_buyer">First-Time Buyer</SelectItem>
                            <SelectItem value="luxury_client">Luxury Client</SelectItem>
                            <SelectItem value="investor">Real Estate Investor</SelectItem>
                            <SelectItem value="urgent_seller">Urgent Seller</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-white font-medium">Property Type</Label>
                        <Select
                          value={customSettings.propertyType}
                          onValueChange={(value) => setCustomSettings(prev => ({ ...prev, propertyType: value }))}
                        >
                          <SelectTrigger className="bg-white/5 border-white/20 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20">
                            <SelectItem value="luxury_condo">Luxury Condo</SelectItem>
                            <SelectItem value="family_home">Family Home</SelectItem>
                            <SelectItem value="investment_property">Investment Property</SelectItem>
                            <SelectItem value="commercial">Commercial</SelectItem>
                            <SelectItem value="waterfront">Waterfront</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Market Conditions & Bot Personality */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-white font-medium">Market Condition</Label>
                        <Select
                          value={customSettings.marketCondition}
                          onValueChange={(value) => setCustomSettings(prev => ({ ...prev, marketCondition: value }))}
                        >
                          <SelectTrigger className="bg-white/5 border-white/20 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20">
                            <SelectItem value="hot_market">Hot Market</SelectItem>
                            <SelectItem value="balanced_market">Balanced Market</SelectItem>
                            <SelectItem value="buyers_market">Buyer's Market</SelectItem>
                            <SelectItem value="rising_rates">Rising Interest Rates</SelectItem>
                            <SelectItem value="luxury_boom">Luxury Boom</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-white font-medium">Jorge's Personality</Label>
                        <Select
                          value={customSettings.botPersonality}
                          onValueChange={(value) => setCustomSettings(prev => ({ ...prev, botPersonality: value }))}
                        >
                          <SelectTrigger className="bg-white/5 border-white/20 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-white/20">
                            <SelectItem value="confrontational">Confrontational (Classic Jorge)</SelectItem>
                            <SelectItem value="supportive">Supportive (Nurturing)</SelectItem>
                            <SelectItem value="analytical">Analytical (Data-Driven)</SelectItem>
                            <SelectItem value="urgent">Urgent (Crisis Mode)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Simulation Settings */}
                    <div className="border-t border-white/10 pt-6">
                      <h4 className="text-white font-medium mb-4">Simulation Settings</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center justify-between">
                          <Label className="text-white text-sm">Auto-advance conversation</Label>
                          <Switch
                            checked={demoState.simulationSettings.autoAdvance}
                            onCheckedChange={(checked) =>
                              demoActions.updateSimulationSettings({ autoAdvance: checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label className="text-white text-sm">Show confidence scores</Label>
                          <Switch
                            checked={demoState.simulationSettings.showConfidence}
                            onCheckedChange={(checked) =>
                              demoActions.updateSimulationSettings({ showConfidence: checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label className="text-white text-sm">Typing indicators</Label>
                          <Switch
                            checked={demoState.simulationSettings.includeTypingIndicators}
                            onCheckedChange={(checked) =>
                              demoActions.updateSimulationSettings({ includeTypingIndicators: checked })
                            }
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label className="text-white text-sm">Display reasoning</Label>
                          <Switch
                            checked={demoState.simulationSettings.displayReasoning}
                            onCheckedChange={(checked) =>
                              demoActions.updateSimulationSettings({ displayReasoning: checked })
                            }
                          />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Control Panel */}
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center">
                      <Zap className="w-5 h-5 mr-2" />
                      Demo Controls
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <DemoControlPanel
                      scenario={demoState.currentScenario}
                      isActive={demoState.isActive}
                      progress={demoState.scenarioProgress}
                      onStart={demoActions.startDemo}
                      onPause={demoActions.pauseDemo}
                      onReset={handleResetConfiguration}
                      onNext={demoActions.nextStep}
                      onPresentationMode={handleStartDemo}
                    />
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </TabsContent>

          {/* Demo Data Tab */}
          <TabsContent value="data" className="space-y-6">
            {demoState.currentScenario && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <SyntheticDataViewer
                  scenario={demoState.currentScenario}
                  properties={demoState.demoProperties}
                  leads={demoState.demoLeads}
                  onRefreshData={demoActions.refreshDemoData}
                />
              </motion.div>
            )}
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview" className="space-y-6">
            {demoState.currentScenario && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center">
                      <Monitor className="w-5 h-5 mr-2" />
                      Demo Preview
                    </CardTitle>
                    <p className="text-gray-300">
                      Review your configured demonstration before presenting to clients
                    </p>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* Scenario Summary */}
                      <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
                        <h4 className="text-blue-300 font-medium mb-2">Scenario Summary</h4>
                        <p className="text-gray-300 text-sm mb-3">{demoState.currentScenario.description}</p>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-gray-400">Duration</div>
                            <div className="text-white">{customSettings.duration} minutes</div>
                          </div>
                          <div>
                            <div className="text-gray-400">Client Type</div>
                            <div className="text-white">{customSettings.clientType.replace('_', ' ')}</div>
                          </div>
                          <div>
                            <div className="text-gray-400">Property Type</div>
                            <div className="text-white">{customSettings.propertyType.replace('_', ' ')}</div>
                          </div>
                          <div>
                            <div className="text-gray-400">Market</div>
                            <div className="text-white">{customSettings.marketCondition.replace('_', ' ')}</div>
                          </div>
                        </div>
                      </div>

                      {/* Conversation Flow Preview */}
                      <div>
                        <h4 className="text-white font-medium mb-3">Conversation Flow</h4>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {demoState.currentScenario.conversationFlow.slice(0, 3).map((step, index) => (
                            <div key={step.id} className="bg-white/5 rounded-lg p-3 border border-white/10">
                              <div className="flex items-center justify-between mb-2">
                                <Badge variant="outline" className="text-xs">
                                  Step {step.stepNumber}
                                </Badge>
                                <span className="text-xs text-gray-400">{step.content.tone}</span>
                              </div>
                              <p className="text-sm text-gray-300">{step.content.message}</p>
                              {step.demoNotes && (
                                <p className="text-xs text-blue-300 mt-2">{step.demoNotes}</p>
                              )}
                            </div>
                          ))}
                          {demoState.currentScenario.conversationFlow.length > 3 && (
                            <div className="text-center text-gray-400 text-sm">
                              + {demoState.currentScenario.conversationFlow.length - 3} more steps
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Final Actions */}
                      <div className="flex items-center justify-between pt-4 border-t border-white/10">
                        <Button
                          variant="outline"
                          onClick={handleResetConfiguration}
                          className="border-white/20 text-white hover:bg-white/10"
                        >
                          <RotateCcw className="w-4 h-4 mr-2" />
                          Reset Configuration
                        </Button>

                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            onClick={() => {
                              const data = demoActions.exportScenarioData();
                              const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                              const url = URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = `jorge-demo-${demoState.currentScenario.id}.json`;
                              a.click();
                            }}
                            className="border-white/20 text-white hover:bg-white/10"
                          >
                            <Download className="w-4 h-4 mr-2" />
                            Export
                          </Button>

                          <Button
                            onClick={handleStartDemo}
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            <PlayCircle className="w-4 h-4 mr-2" />
                            Start Presentation
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </TabsContent>
        </Tabs>

        {/* Error Display */}
        {demoState.error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6"
          >
            <Card className="border-red-500/20 bg-red-500/5">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-red-400">
                  <Target className="w-5 h-5" />
                  <span className="font-semibold">Configuration Error:</span>
                  <span>{demoState.error}</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  );
}