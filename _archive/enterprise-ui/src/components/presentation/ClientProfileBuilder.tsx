// Client Profile Builder Component
// Creates detailed client profiles for accurate ROI calculations

'use client';

import { useState } from 'react';
import {
  User,
  DollarSign,
  Clock,
  Target,
  Building,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Plus,
  X
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { type ClientProfile, ROIEngine } from '@/lib/presentation/ROIEngine';

interface ClientProfileBuilderProps {
  profile: ClientProfile | null;
  onProfileChange: (profile: ClientProfile) => void;
  onPropertyUpdate: (updates: Partial<ClientProfile>) => void;
  marketInsights: any;
}

export function ClientProfileBuilder({
  profile,
  onProfileChange,
  onPropertyUpdate,
  marketInsights
}: ClientProfileBuilderProps) {
  const [formData, setFormData] = useState({
    name: profile?.name || '',
    propertyBudget: profile?.propertyBudget?.toString() || '',
    marketSegment: profile?.marketSegment || 'mid-market',
    urgency: profile?.urgency || 'medium',
  });

  const [customPainPoints, setCustomPainPoints] = useState<string[]>(
    profile?.painPoints || []
  );
  const [customGoals, setCustomGoals] = useState<string[]>(
    profile?.goals || []
  );

  const [newPainPoint, setNewPainPoint] = useState('');
  const [newGoal, setNewGoal] = useState('');

  const handleFormChange = (field: string, value: string) => {
    const updatedData = { ...formData, [field]: value };
    setFormData(updatedData);

    if (profile) {
      onPropertyUpdate({
        [field]: field === 'propertyBudget' ? parseInt(value) || 0 : value
      });
    }
  };

  const handleCreateProfile = () => {
    const budget = parseInt(formData.propertyBudget) || 0;

    if (!formData.name || budget <= 0) {
      return;
    }

    const newProfile = ROIEngine.generateClientProfile(
      formData.name,
      budget,
      formData.marketSegment as ClientProfile['marketSegment'],
      formData.urgency as ClientProfile['urgency']
    );

    // Override with custom pain points and goals if provided
    newProfile.painPoints = customPainPoints.length > 0 ? customPainPoints : newProfile.painPoints;
    newProfile.goals = customGoals.length > 0 ? customGoals : newProfile.goals;

    onProfileChange(newProfile);
  };

  const addPainPoint = () => {
    if (newPainPoint.trim()) {
      const updated = [...customPainPoints, newPainPoint.trim()];
      setCustomPainPoints(updated);
      setNewPainPoint('');

      if (profile) {
        onPropertyUpdate({ painPoints: updated });
      }
    }
  };

  const addGoal = () => {
    if (newGoal.trim()) {
      const updated = [...customGoals, newGoal.trim()];
      setCustomGoals(updated);
      setNewGoal('');

      if (profile) {
        onPropertyUpdate({ goals: updated });
      }
    }
  };

  const removePainPoint = (index: number) => {
    const updated = customPainPoints.filter((_, i) => i !== index);
    setCustomPainPoints(updated);

    if (profile) {
      onPropertyUpdate({ painPoints: updated });
    }
  };

  const removeGoal = (index: number) => {
    const updated = customGoals.filter((_, i) => i !== index);
    setCustomGoals(updated);

    if (profile) {
      onPropertyUpdate({ goals: updated });
    }
  };

  const insights = marketInsights[formData.marketSegment as keyof typeof marketInsights];
  const isFormValid = formData.name && parseInt(formData.propertyBudget) > 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Profile Form */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5 text-blue-600" />
            Client Profile Builder
          </CardTitle>
          <p className="text-gray-600">
            Create a detailed client profile to generate accurate ROI calculations
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Client Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleFormChange('name', e.target.value)}
                placeholder="Enter client name"
              />
            </div>

            <div>
              <Label htmlFor="budget">Property Budget</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                <Input
                  id="budget"
                  type="number"
                  className="pl-10"
                  value={formData.propertyBudget}
                  onChange={(e) => handleFormChange('propertyBudget', e.target.value)}
                  placeholder="500000"
                />
              </div>
            </div>
          </div>

          {/* Market Segment */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="segment">Market Segment</Label>
              <Select
                value={formData.marketSegment}
                onValueChange={(value) => handleFormChange('marketSegment', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="luxury">
                    <div className="flex items-center gap-2">
                      <Building className="w-4 h-4" />
                      Luxury ($2M+)
                    </div>
                  </SelectItem>
                  <SelectItem value="mid-market">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      Mid-Market ($300K-$800K)
                    </div>
                  </SelectItem>
                  <SelectItem value="first-time">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      First-Time ($200K-$400K)
                    </div>
                  </SelectItem>
                  <SelectItem value="investor">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Investor ($500K+)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="urgency">Urgency Level</Label>
              <Select
                value={formData.urgency}
                onValueChange={(value) => handleFormChange('urgency', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-red-500" />
                      High - Immediate Action
                    </div>
                  </SelectItem>
                  <SelectItem value="medium">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-yellow-500" />
                      Medium - Active Search
                    </div>
                  </SelectItem>
                  <SelectItem value="low">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      Low - Exploring Options
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Pain Points */}
          <div>
            <Label>Pain Points & Challenges</Label>
            <p className="text-sm text-gray-600 mb-3">
              Identify specific challenges this client faces
            </p>

            <div className="flex gap-2 mb-3">
              <Input
                value={newPainPoint}
                onChange={(e) => setNewPainPoint(e.target.value)}
                placeholder="Add pain point..."
                onKeyPress={(e) => e.key === 'Enter' && addPainPoint()}
              />
              <Button onClick={addPainPoint} size="sm">
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {customPainPoints.map((painPoint, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="bg-red-50 text-red-700 border-red-200 pr-1"
                >
                  {painPoint}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-2"
                    onClick={() => removePainPoint(index)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Goals */}
          <div>
            <Label>Goals & Objectives</Label>
            <p className="text-sm text-gray-600 mb-3">
              Define what success looks like for this client
            </p>

            <div className="flex gap-2 mb-3">
              <Input
                value={newGoal}
                onChange={(e) => setNewGoal(e.target.value)}
                placeholder="Add goal..."
                onKeyPress={(e) => e.key === 'Enter' && addGoal()}
              />
              <Button onClick={addGoal} size="sm">
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {customGoals.map((goal, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="bg-green-50 text-green-700 border-green-200 pr-1"
                >
                  {goal}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-2"
                    onClick={() => removeGoal(index)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Action Button */}
          <div className="flex justify-end">
            <Button
              onClick={handleCreateProfile}
              disabled={!isFormValid}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {profile ? 'Update Profile' : 'Create Profile'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Market Insights */}
      <div className="space-y-6">
        {/* Segment Insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Market Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {insights && (
              <>
                <div>
                  <Label>Average Property Value</Label>
                  <p className="text-2xl font-bold text-green-600">
                    {ROIEngine.formatCurrency(insights.avgPropertyValue)}
                  </p>
                </div>

                <div>
                  <Label>Average Days on Market</Label>
                  <p className="text-xl font-semibold">
                    {insights.avgDaysOnMarket} days
                  </p>
                </div>

                <div>
                  <Label>Jorge's Advantage</Label>
                  <p className="text-sm text-gray-700">
                    {insights.jorgeAdvantage}
                  </p>
                </div>

                <div>
                  <Label>Key Success Factors</Label>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {insights.keyFactors.map((factor: string) => (
                      <Badge key={factor} variant="secondary" className="text-xs">
                        {factor}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Profile Summary */}
        {profile && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                Profile Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Client:</span>
                <span className="font-semibold">{profile.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Budget:</span>
                <span className="font-semibold">
                  {ROIEngine.formatCurrency(profile.propertyBudget)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Segment:</span>
                <Badge variant="outline">
                  {profile.marketSegment}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Urgency:</span>
                <Badge
                  variant="outline"
                  className={
                    profile.urgency === 'high'
                      ? 'border-red-200 text-red-700'
                      : profile.urgency === 'medium'
                      ? 'border-yellow-200 text-yellow-700'
                      : 'border-green-200 text-green-700'
                  }
                >
                  {profile.urgency}
                </Badge>
              </div>

              <div className="pt-2 border-t">
                <span className="text-sm text-gray-600">
                  Ready for ROI calculation
                </span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}