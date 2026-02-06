// Jorge's Synthetic Data Viewer
// Client-safe display of demo properties, leads, and market scenarios

'use client';

import { useState } from 'react';
import {
  Home,
  Users,
  BarChart3,
  RefreshCw,
  Download,
  Shield,
  Eye,
  DollarSign,
  MapPin,
  Calendar,
  Phone,
  Mail,
  TrendingUp
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import type { DemoScenario } from '@/lib/demo/ScenarioEngine';
import type { SyntheticProperty, SyntheticLead } from '@/lib/demo/DemoDataGenerator';

interface SyntheticDataViewerProps {
  scenario: DemoScenario;
  properties: SyntheticProperty[];
  leads: SyntheticLead[];
  onRefreshData: () => void;
}

export function SyntheticDataViewer({
  scenario,
  properties,
  leads,
  onRefreshData
}: SyntheticDataViewerProps) {
  const [selectedProperty, setSelectedProperty] = useState<SyntheticProperty | null>(null);
  const [selectedLead, setSelectedLead] = useState<SyntheticLead | null>(null);

  const handleExportData = () => {
    const exportData = {
      scenario: {
        id: scenario.id,
        name: scenario.name,
        category: scenario.category
      },
      properties: properties.map(p => ({
        ...p,
        note: 'SYNTHETIC DATA - Safe for client demonstrations'
      })),
      leads: leads.map(l => ({
        ...l,
        note: 'SYNTHETIC DATA - Safe for client demonstrations'
      })),
      timestamp: new Date().toISOString(),
      disclaimer: 'All data in this file is synthetic and generated for demonstration purposes only.'
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `jorge-demo-data-${scenario.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getUrgencyColor = (urgency: string) => {
    const colors = {
      high: 'bg-red-500/10 text-red-400 border-red-500/30',
      medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      low: 'bg-green-500/10 text-green-400 border-green-500/30'
    };
    return colors[urgency as keyof typeof colors] || 'bg-gray-500/10 text-gray-400 border-gray-500/30';
  };

  const getTemperatureColor = (temperature: number) => {
    if (temperature >= 75) return 'text-red-400';
    if (temperature >= 50) return 'text-yellow-400';
    return 'text-blue-400';
  };

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-white mb-2">Demo Data Overview</h3>
          <p className="text-gray-300">
            Client-safe synthetic data for professional demonstrations
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30">
            <Shield className="w-4 h-4 mr-1" />
            100% Synthetic
          </Badge>

          <Button
            variant="outline"
            size="sm"
            onClick={onRefreshData}
            className="border-white/20 text-white hover:bg-white/10"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportData}
            className="border-white/20 text-white hover:bg-white/10"
          >
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Data Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-400 mb-1">{properties.length}</div>
            <div className="text-sm text-gray-300">Demo Properties</div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-400 mb-1">{leads.length}</div>
            <div className="text-sm text-gray-300">Client Personas</div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-400 mb-1">
              {formatCurrency(properties.reduce((sum, p) => sum + p.price, 0) / properties.length)}
            </div>
            <div className="text-sm text-gray-300">Avg Property Value</div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-yellow-400 mb-1">
              {Math.round(leads.reduce((sum, l) => sum + l.temperature, 0) / leads.length)}
            </div>
            <div className="text-sm text-gray-300">Avg Lead Temperature</div>
          </CardContent>
        </Card>
      </div>

      {/* Data Tabs */}
      <Tabs defaultValue="properties" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 bg-white/5 border border-white/10">
          <TabsTrigger value="properties" className="data-[state=active]:bg-white/10">
            <Home className="w-4 h-4 mr-2" />
            Properties ({properties.length})
          </TabsTrigger>
          <TabsTrigger value="leads" className="data-[state=active]:bg-white/10">
            <Users className="w-4 h-4 mr-2" />
            Leads ({leads.length})
          </TabsTrigger>
          <TabsTrigger value="market" className="data-[state=active]:bg-white/10">
            <BarChart3 className="w-4 h-4 mr-2" />
            Market Context
          </TabsTrigger>
        </TabsList>

        {/* Properties Tab */}
        <TabsContent value="properties" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Properties List */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-white">Synthetic Properties</h4>
              {properties.map((property, index) => (
                <motion.div
                  key={property.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card
                    className={`cursor-pointer transition-all duration-200 ${
                      selectedProperty?.id === property.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'bg-white/5 border-white/10 hover:border-white/30'
                    }`}
                    onClick={() => setSelectedProperty(property)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h5 className="font-semibold text-white">{property.address}</h5>
                          <p className="text-sm text-gray-400">{property.type}</p>
                        </div>
                        <Badge variant="outline" className={getUrgencyColor(property.urgency)}>
                          {property.urgency} urgency
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="text-gray-400">Price</div>
                          <div className="font-semibold text-white">{formatCurrency(property.price)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Market Trend</div>
                          <div className="text-blue-400">{property.marketData.marketTrend}</div>
                        </div>
                      </div>

                      <p className="text-xs text-gray-300 mt-2 line-clamp-2">{property.story}</p>

                      {property.demoContext && (
                        <div className="mt-2">
                          <Badge variant="outline" className="text-xs bg-purple-500/10 text-purple-400 border-purple-500/30">
                            <Eye className="w-3 h-3 mr-1" />
                            Demo Context
                          </Badge>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>

            {/* Property Details */}
            <div>
              {selectedProperty ? (
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center">
                      <Home className="w-5 h-5 mr-2" />
                      Property Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h5 className="font-semibold text-white mb-2">{selectedProperty.address}</h5>
                      <p className="text-gray-300 text-sm">{selectedProperty.story}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-gray-400">Price</div>
                        <div className="text-white font-semibold">{formatCurrency(selectedProperty.price)}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Type</div>
                        <div className="text-white">{selectedProperty.type}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Market Value</div>
                        <div className="text-white">{formatCurrency(selectedProperty.marketData.estimatedValue)}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Days on Market</div>
                        <div className="text-white">{selectedProperty.marketData.daysOnMarket}</div>
                      </div>
                    </div>

                    <div>
                      <div className="text-gray-400 text-sm mb-2">Features</div>
                      <div className="space-y-1">
                        {selectedProperty.features.map((feature, i) => (
                          <div key={i} className="flex items-center justify-between text-sm">
                            <span className="text-gray-300">{feature.name}</span>
                            <span className="text-white">{feature.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {selectedProperty.demoContext && (
                      <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/20">
                        <div className="text-purple-300 text-sm font-medium mb-1">Demo Context</div>
                        <p className="text-purple-200 text-xs">{selectedProperty.demoContext}</p>
                      </div>
                    )}

                    <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
                      <div className="flex items-center gap-2 text-green-300 text-sm">
                        <Shield className="w-4 h-4" />
                        <span className="font-medium">Synthetic Data Confirmation</span>
                      </div>
                      <p className="text-green-200 text-xs mt-1">
                        This property data is 100% synthetic and safe for client demonstrations.
                        No real addresses, pricing, or client information is used.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-white/5 border-white/10">
                  <CardContent className="p-8 text-center">
                    <Home className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-400">Select a property to view details</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Leads Tab */}
        <TabsContent value="leads" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Leads List */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-white">Client Personas</h4>
              {leads.map((lead, index) => (
                <motion.div
                  key={lead.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card
                    className={`cursor-pointer transition-all duration-200 ${
                      selectedLead?.id === lead.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'bg-white/5 border-white/10 hover:border-white/30'
                    }`}
                    onClick={() => setSelectedLead(lead)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h5 className="font-semibold text-white">{lead.name}</h5>
                          <p className="text-sm text-gray-400 capitalize">{lead.type} - {lead.persona.replace('_', ' ')}</p>
                        </div>
                        <div className="text-right">
                          <div className={`text-sm font-semibold ${getTemperatureColor(lead.temperature)}`}>
                            {lead.temperature}°
                          </div>
                          <div className="text-xs text-gray-400">Temperature</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="text-gray-400">Budget</div>
                          <div className="font-semibold text-white">{formatCurrency(lead.budget)}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Urgency</div>
                          <div className="text-blue-400 capitalize">{lead.urgency}</div>
                        </div>
                      </div>

                      <p className="text-xs text-gray-300 mt-2 line-clamp-2">{lead.story}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>

            {/* Lead Details */}
            <div>
              {selectedLead ? (
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center">
                      <Users className="w-5 h-5 mr-2" />
                      Client Profile
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h5 className="font-semibold text-white mb-2">{selectedLead.name}</h5>
                      <p className="text-gray-300 text-sm">{selectedLead.story}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-gray-400">Type</div>
                        <div className="text-white capitalize">{selectedLead.type}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Budget</div>
                        <div className="text-white">{formatCurrency(selectedLead.budget)}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Temperature</div>
                        <div className={getTemperatureColor(selectedLead.temperature)}>
                          {selectedLead.temperature}° ({selectedLead.urgency})
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400">Timeline</div>
                        <div className="text-white">{selectedLead.preferences.timeline}</div>
                      </div>
                    </div>

                    <div>
                      <div className="text-gray-400 text-sm mb-2">Contact Information</div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <Phone className="w-4 h-4 text-gray-400" />
                          <span className="text-white">{selectedLead.contactInfo.phone}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Mail className="w-4 h-4 text-gray-400" />
                          <span className="text-white">{selectedLead.contactInfo.email}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-gray-400 text-sm mb-2">Preferences</div>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-gray-400">Property Types:</span>
                          <span className="text-white ml-2">{selectedLead.preferences.propertyTypes.join(', ')}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Price Range:</span>
                          <span className="text-white ml-2">
                            {formatCurrency(selectedLead.preferences.priceRange.min)} - {formatCurrency(selectedLead.preferences.priceRange.max)}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-400">Locations:</span>
                          <span className="text-white ml-2">{selectedLead.preferences.locations.join(', ')}</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
                      <div className="flex items-center gap-2 text-green-300 text-sm">
                        <Shield className="w-4 h-4" />
                        <span className="font-medium">Synthetic Data Confirmation</span>
                      </div>
                      <p className="text-green-200 text-xs mt-1">
                        This client profile is 100% synthetic and safe for demonstrations.
                        No real contact information or client data is used.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-white/5 border-white/10">
                  <CardContent className="p-8 text-center">
                    <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-400">Select a client to view profile details</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Market Context Tab */}
        <TabsContent value="market" className="space-y-4">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle className="text-white flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                Market Context: {scenario.marketContext.name}
              </CardTitle>
              <p className="text-gray-300">{scenario.marketContext.context}</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h5 className="text-white font-semibold mb-3">Market Trends</h5>
                  <div className="space-y-2">
                    {scenario.marketContext.trends.map((trend, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <TrendingUp className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                        <span className="text-gray-300">{trend}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h5 className="text-white font-semibold mb-3">Opportunities</h5>
                  <div className="space-y-2">
                    {scenario.marketContext.opportunities.map((opportunity, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-gray-300">{opportunity}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h5 className="text-white font-semibold mb-3">Challenges</h5>
                  <div className="space-y-2">
                    {scenario.marketContext.challenges.map((challenge, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <div className="w-2 h-2 bg-red-400 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-gray-300">{challenge}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
                <h5 className="text-blue-300 font-semibold mb-2">Jorge's Competitive Advantage</h5>
                <p className="text-blue-200 text-sm">{scenario.marketContext.jorgeAdvantage}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default SyntheticDataViewer;