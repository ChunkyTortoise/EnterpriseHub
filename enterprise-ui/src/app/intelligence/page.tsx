'use client';

import { useState } from 'react';
import { Card, Title, Text, Flex, Button, Badge, TabGroup, TabList, Tab, TabPanels, TabPanel } from '@tremor/react';
import { Brain, Home, TrendingUp, Activity } from 'lucide-react';
import { PropertyIntelligenceDashboard } from '@/components/property-intelligence/PropertyIntelligenceDashboard';
import { BusinessIntelligenceDashboard } from '@/components/BusinessIntelligenceDashboard';

export default function IntelligencePage() {
  const [selectedTab, setSelectedTab] = useState(0);

  return (
    <div className="min-h-screen bg-[#0f0f0f] p-6">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <Card className="bg-slate-900 border-slate-800 mb-6">
          <Flex justifyContent="between" alignItems="start">
            <div>
              <Title className="text-slate-100 text-3xl flex items-center space-x-3">
                <Brain className="h-8 w-8 text-blue-400" />
                <span>Jorge's Intelligence Center</span>
              </Title>
              <Text className="text-slate-400 mt-2 text-lg">
                Unified intelligence dashboard with property analytics and business intelligence
              </Text>
            </div>
            <Badge color="blue" size="lg">
              <Activity className="h-4 w-4 mr-1" />
              Phase 7 Active
            </Badge>
          </Flex>
        </Card>

        {/* Intelligence Tabs */}
        <Card className="bg-slate-900 border-slate-800">
          <TabGroup selectedIndex={selectedTab} onIndexChange={setSelectedTab}>
            <TabList className="mb-6">
              <Tab icon={TrendingUp}>Advanced Business Intelligence</Tab>
              <Tab icon={Home}>Property Intelligence</Tab>
            </TabList>

            <TabPanels>
              {/* Advanced Business Intelligence */}
              <TabPanel>
                <BusinessIntelligenceDashboard
                  locationId="jorge-platform"
                  autoRefresh={true}
                  showRealTimeAlerts={true}
                />
              </TabPanel>

              {/* Property Intelligence */}
              <TabPanel>
                <PropertyIntelligenceDashboard propertyId="demo-property" />
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </Card>
      </div>
    </div>
  );
}