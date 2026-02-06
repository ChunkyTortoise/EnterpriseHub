// Jorge's Demo Scenario Selector Component
// Professional scenario selection interface with category filtering

'use client';

import { useState } from 'react';
import {
  Target,
  Users,
  BarChart3,
  Brain,
  Clock,
  PlayCircle,
  Star,
  TrendingUp,
  Shield
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { motion } from 'framer-motion';
import type { DemoScenario } from '@/lib/demo/ScenarioEngine';

interface DemoScenarioSelectorProps {
  scenarios: DemoScenario[];
  categorized: {
    seller_qualification: DemoScenario[];
    buyer_nurture: DemoScenario[];
    market_intelligence: DemoScenario[];
    cross_bot_coordination: DemoScenario[];
  };
  selectedScenario: DemoScenario | null;
  onScenarioSelect: (scenarioId: string) => void;
  isLoading?: boolean;
}

export function DemoScenarioSelector({
  scenarios,
  categorized,
  selectedScenario,
  onScenarioSelect,
  isLoading = false
}: DemoScenarioSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categoryConfig = {
    seller_qualification: {
      name: 'Seller Qualification',
      icon: Target,
      color: 'bg-red-500/10 border-red-500/30 text-red-300',
      description: 'Jorge\'s confrontational qualification methodology'
    },
    buyer_nurture: {
      name: 'Buyer Nurture',
      icon: Users,
      color: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
      description: '3-7-30 day automation with voice integration'
    },
    market_intelligence: {
      name: 'Market Intelligence',
      icon: BarChart3,
      color: 'bg-green-500/10 border-green-500/30 text-green-300',
      description: 'Real-time CMA and market analysis'
    },
    cross_bot_coordination: {
      name: 'Bot Coordination',
      icon: Brain,
      color: 'bg-purple-500/10 border-purple-500/30 text-purple-300',
      description: 'Seamless handoffs between specialized bots'
    }
  };

  const filteredScenarios = scenarios.filter(scenario => {
    const matchesSearch = scenario.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scenario.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || scenario.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getScenarioComplexity = (scenario: DemoScenario) => {
    if (scenario.duration <= 5) return { label: 'Quick', color: 'text-green-400' };
    if (scenario.duration <= 10) return { label: 'Standard', color: 'text-blue-400' };
    return { label: 'Comprehensive', color: 'text-purple-400' };
  };

  const getScenarioPopularity = (scenarioId: string) => {
    // Simulate popularity scores - in real app would come from analytics
    const popularScenarios = ['hot_seller_qualification', 'buyer_nurture_sequence'];
    return popularScenarios.includes(scenarioId);
  };

  return (
    <div className="space-y-6">
      {/* Search and Filter Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        <div className="flex-1">
          <Input
            placeholder="Search scenarios by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-white/5 border-white/20 text-white placeholder-gray-400"
          />
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={selectedCategory === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedCategory('all')}
            className={selectedCategory === 'all' ? 'bg-blue-600' : 'border-white/20 text-white hover:bg-white/10'}
          >
            All ({scenarios.length})
          </Button>
          {Object.entries(categoryConfig).map(([key, config]) => {
            const Icon = config.icon;
            const count = categorized[key as keyof typeof categorized].length;

            return (
              <Button
                key={key}
                variant={selectedCategory === key ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(key)}
                className={
                  selectedCategory === key
                    ? 'bg-blue-600'
                    : 'border-white/20 text-white hover:bg-white/10'
                }
              >
                <Icon className="w-4 h-4 mr-1" />
                {config.name} ({count})
              </Button>
            );
          })}
        </div>
      </div>

      {/* Category Overview (when category is selected) */}
      {selectedCategory !== 'all' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className={`${categoryConfig[selectedCategory as keyof typeof categoryConfig].color} border`}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                {(() => {
                  const Icon = categoryConfig[selectedCategory as keyof typeof categoryConfig].icon;
                  return <Icon className="w-6 h-6" />;
                })()}
                <div>
                  <h3 className="font-semibold">
                    {categoryConfig[selectedCategory as keyof typeof categoryConfig].name}
                  </h3>
                  <p className="text-sm opacity-80">
                    {categoryConfig[selectedCategory as keyof typeof categoryConfig].description}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredScenarios.map((scenario, index) => {
          const isSelected = selectedScenario?.id === scenario.id;
          const complexity = getScenarioComplexity(scenario);
          const isPopular = getScenarioPopularity(scenario.id);
          const categoryConfig_local = categoryConfig[scenario.category as keyof typeof categoryConfig];
          const CategoryIcon = categoryConfig_local.icon;

          return (
            <motion.div
              key={scenario.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
            >
              <Card
                className={`
                  cursor-pointer transition-all duration-300 h-full
                  ${isSelected
                    ? 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/20'
                    : 'bg-white/5 border-white/10 hover:border-white/30 hover:bg-white/10'
                  }
                `}
                onClick={() => onScenarioSelect(scenario.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <CategoryIcon className="w-5 h-5 text-blue-400" />
                      <Badge variant="outline" className="text-xs border-gray-500">
                        {scenario.category.replace('_', ' ')}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-1">
                      {isPopular && (
                        <Badge variant="outline" className="text-xs bg-yellow-500/10 text-yellow-400 border-yellow-500/30">
                          <Star className="w-3 h-3 mr-1" />
                          Popular
                        </Badge>
                      )}
                      <div className="flex items-center gap-1 text-xs text-gray-400">
                        <Clock className="w-3 h-3" />
                        <span>{scenario.duration} min</span>
                      </div>
                    </div>
                  </div>

                  <CardTitle className="text-white text-lg leading-tight">
                    {scenario.name}
                  </CardTitle>
                </CardHeader>

                <CardContent className="pt-0 space-y-4">
                  <p className="text-gray-300 text-sm leading-relaxed line-clamp-2">
                    {scenario.description}
                  </p>

                  {/* Scenario Highlights */}
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-gray-400 mb-1">Jorge Advantages:</div>
                      <div className="space-y-1">
                        {scenario.jorgeAdvantages.slice(0, 2).map((advantage, i) => (
                          <div key={i} className="text-xs text-blue-300 flex items-start">
                            <div className="w-1 h-1 bg-blue-400 rounded-full mr-2 mt-1.5 flex-shrink-0"></div>
                            <span className="line-clamp-1">{advantage}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs text-gray-400 mb-1">Client Benefits:</div>
                      <div className="space-y-1">
                        {scenario.clientBenefits.slice(0, 2).map((benefit, i) => (
                          <div key={i} className="text-xs text-green-300 flex items-start">
                            <div className="w-1 h-1 bg-green-400 rounded-full mr-2 mt-1.5 flex-shrink-0"></div>
                            <span className="line-clamp-1">{benefit}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Scenario Metrics */}
                  <div className="flex items-center justify-between pt-2 border-t border-white/10">
                    <div className="flex items-center gap-3 text-xs">
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3 text-gray-400" />
                        <span className="text-gray-400">{scenario.participants.length} participants</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-gray-400" />
                        <span className={complexity.color}>{complexity.label}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      <Shield className="w-3 h-3 text-green-400" />
                      <span className="text-xs text-green-400">Synthetic Data</span>
                    </div>
                  </div>

                  {/* Action Button */}
                  <Button
                    size="sm"
                    disabled={isLoading}
                    className={`
                      w-full mt-4
                      ${isSelected
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-white/5 hover:bg-white/10 border border-white/20 text-white'
                      }
                    `}
                  >
                    {isLoading ? (
                      <div className="flex items-center">
                        <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                        Loading...
                      </div>
                    ) : isSelected ? (
                      <div className="flex items-center">
                        <PlayCircle className="w-4 h-4 mr-2" />
                        Selected Scenario
                      </div>
                    ) : (
                      <div className="flex items-center">
                        <Target className="w-4 h-4 mr-2" />
                        Select Scenario
                      </div>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredScenarios.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="bg-white/5 border-white/10">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-gray-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Target className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">No scenarios found</h3>
              <p className="text-gray-400 mb-4">
                Try adjusting your search terms or category filters.
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  setSearchTerm('');
                  setSelectedCategory('all');
                }}
                className="border-white/20 text-white hover:bg-white/10"
              >
                Clear Filters
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Quick Stats */}
      {filteredScenarios.length > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-400 pt-4 border-t border-white/10">
          <div>
            Showing {filteredScenarios.length} of {scenarios.length} scenarios
          </div>
          {searchTerm && (
            <div>
              Search: "{searchTerm}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default DemoScenarioSelector;