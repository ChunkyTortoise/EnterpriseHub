/**
 * Lead Bot Action Controls Component
 *
 * Provides manual controls for Lead Bot sequence actions
 * Allows testing and recovery operations for sequences
 */

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  MessageSquare,
  Phone,
  Mail,
  Play,
  Zap,
  Settings,
  TestTube,
  AlertTriangle,
  CheckCircle,
  RotateCcw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { leadBotApi, type ManualTriggerPayload } from '@/lib/api/lead-bot-api';
import { useToast } from '@/hooks/use-toast';

interface LeadBotActionControlsProps {
  leadId: string;
  className?: string;
  disabled?: boolean;
  onActionTriggered?: (action: string, result: any) => void;
}

export function LeadBotActionControls({
  leadId,
  className,
  disabled = false,
  onActionTriggered
}: LeadBotActionControlsProps) {
  const [selectedDay, setSelectedDay] = useState<'DAY_3' | 'DAY_7' | 'DAY_14' | 'DAY_30'>('DAY_3');
  const [selectedAction, setSelectedAction] = useState<'sms' | 'call' | 'email'>('sms');
  const [loading, setLoading] = useState<string | null>(null);
  const { toast } = useToast();

  // Available actions for each sequence day
  const sequenceActions = {
    DAY_3: [
      { value: 'sms', label: 'SMS Message', icon: MessageSquare, description: 'Send initial SMS follow-up' }
    ],
    DAY_7: [
      { value: 'call', label: 'Voice Call', icon: Phone, description: 'Make voice call with Retell AI' },
      { value: 'sms', label: 'SMS Backup', icon: MessageSquare, description: 'Send SMS if call fails' }
    ],
    DAY_14: [
      { value: 'email', label: 'Email Follow-up', icon: Mail, description: 'Send detailed email with CMA' }
    ],
    DAY_30: [
      { value: 'sms', label: 'Final SMS', icon: MessageSquare, description: 'Send final follow-up SMS' }
    ]
  };

  // Get available actions for selected day
  const availableActions = sequenceActions[selectedDay] || [];

  // Handle manual trigger
  const handleManualTrigger = async () => {
    const payload: ManualTriggerPayload = {
      lead_id: leadId,
      sequence_day: selectedDay,
      action_type: selectedAction
    };

    setLoading('trigger');
    try {
      const result = await leadBotApi.manualTrigger(payload);

      if (result.success) {
        toast({
          title: 'Action triggered successfully',
          description: result.message
        });
        onActionTriggered?.('manual_trigger', result);
      } else {
        toast({
          title: 'Action failed',
          description: result.message,
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to trigger action',
        description: 'Please check your connection and try again',
        variant: 'destructive'
      });
    } finally {
      setLoading(null);
    }
  };

  // Handle test sequence
  const handleTestSequence = async () => {
    setLoading('test');
    try {
      const result = await leadBotApi.createTestSequence(leadId);

      if (result.success) {
        toast({
          title: 'Test sequence created',
          description: `Test sequence started for ${result.lead_id}`
        });
        onActionTriggered?.('test_sequence', result);
      } else {
        toast({
          title: 'Test sequence failed',
          description: 'Please check the scheduler status',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to create test sequence',
        description: 'Please check your connection and try again',
        variant: 'destructive'
      });
    } finally {
      setLoading(null);
    }
  };

  // Handle scheduler restart
  const handleSchedulerRestart = async () => {
    setLoading('restart');
    try {
      const result = await leadBotApi.restartScheduler();

      if (result.success) {
        toast({
          title: 'Scheduler restarted',
          description: result.message
        });
        onActionTriggered?.('scheduler_restart', result);
      } else {
        toast({
          title: 'Scheduler restart failed',
          description: result.error || 'Unknown error',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to restart scheduler',
        description: 'Please contact support if this persists',
        variant: 'destructive'
      });
    } finally {
      setLoading(null);
    }
  };

  // Update selected action when day changes
  const handleDayChange = (day: typeof selectedDay) => {
    setSelectedDay(day);
    const dayActions = sequenceActions[day];
    if (dayActions.length > 0 && !dayActions.find(a => a.value === selectedAction)) {
      setSelectedAction(dayActions[0].value as typeof selectedAction);
    }
  };

  const selectedActionDetails = availableActions.find(a => a.value === selectedAction);
  const Icon = selectedActionDetails?.icon || MessageSquare;

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Manual Action Controls
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Quick Test Actions */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm">Quick Actions</h4>

          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleTestSequence}
              disabled={disabled || loading === 'test'}
              className="flex items-center gap-2"
            >
              <TestTube className="h-4 w-4" />
              {loading === 'test' ? 'Creating...' : 'Test Sequence'}
            </Button>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={disabled || loading === 'restart'}
                  className="flex items-center gap-2 text-orange-600 border-orange-200 hover:bg-orange-50"
                >
                  <RotateCcw className="h-4 w-4" />
                  {loading === 'restart' ? 'Restarting...' : 'Restart Scheduler'}
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Restart Scheduler</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will restart the Lead Bot scheduler, which may interrupt running sequences.
                    Are you sure you want to continue?
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleSchedulerRestart}>
                    Restart Scheduler
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {/* Manual Trigger Controls */}
        <div className="space-y-4">
          <h4 className="font-medium text-sm">Manual Trigger</h4>

          {/* Sequence Day Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Sequence Day</label>
            <Select value={selectedDay} onValueChange={handleDayChange} disabled={disabled}>
              <SelectTrigger>
                <SelectValue placeholder="Select sequence day" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DAY_3">Day 3 - Initial Follow-up</SelectItem>
                <SelectItem value="DAY_7">Day 7 - Voice Call</SelectItem>
                <SelectItem value="DAY_14">Day 14 - Email with CMA</SelectItem>
                <SelectItem value="DAY_30">Day 30 - Final Follow-up</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Action Type Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Action Type</label>
            <Select
              value={selectedAction}
              onValueChange={(value) => setSelectedAction(value as typeof selectedAction)}
              disabled={disabled}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select action type" />
              </SelectTrigger>
              <SelectContent>
                {availableActions.map((action) => {
                  const ActionIcon = action.icon;
                  return (
                    <SelectItem key={action.value} value={action.value}>
                      <div className="flex items-center gap-2">
                        <ActionIcon className="h-4 w-4" />
                        {action.label}
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>

            {/* Action Description */}
            {selectedActionDetails && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-blue-50 rounded-lg border border-blue-200"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-blue-900">
                  <Icon className="h-4 w-4" />
                  {selectedActionDetails.label}
                </div>
                <p className="text-sm text-blue-800 mt-1">
                  {selectedActionDetails.description}
                </p>
              </motion.div>
            )}
          </div>

          {/* Trigger Button */}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                className="w-full"
                disabled={disabled || !selectedActionDetails || loading === 'trigger'}
              >
                <Zap className="h-4 w-4 mr-2" />
                {loading === 'trigger' ? 'Triggering Action...' : 'Trigger Action'}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  Confirm Manual Trigger
                </AlertDialogTitle>
                <AlertDialogDescription>
                  You are about to manually trigger a <strong>{selectedActionDetails?.label}</strong> for <strong>{selectedDay.replace('DAY_', 'Day ')}</strong>.
                  <br /><br />
                  This will execute the action immediately, bypassing the normal sequence timing.
                  The action will be logged in the sequence timeline.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleManualTrigger}>
                  <Zap className="h-4 w-4 mr-2" />
                  Trigger Action
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        {/* Warning Notice */}
        <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="flex items-center gap-2 text-sm font-medium text-yellow-900">
            <AlertTriangle className="h-4 w-4" />
            Testing & Recovery Only
          </div>
          <p className="text-sm text-yellow-800 mt-1">
            These controls are for testing and error recovery. Normal sequences run automatically.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}