/**
 * Lead Bot Sequence Progress Component
 *
 * Displays 3-7-30 day sequence progress with real-time updates
 * Shows current status, next actions, and engagement metrics
 */

'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  CheckCircle,
  AlertCircle,
  Phone,
  Mail,
  MessageSquare,
  Play,
  Pause,
  Square,
  RotateCcw,
  TrendingUp,
  Calendar,
  User
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { leadBotApi, type SequenceStatusResponse } from '@/lib/api/lead-bot-api';
import { useToast } from '@/hooks/use-toast';

interface LeadBotSequenceProgressProps {
  leadId: string;
  className?: string;
  onSequenceUpdate?: (status: SequenceStatusResponse) => void;
}

export function LeadBotSequenceProgress({
  leadId,
  className,
  onSequenceUpdate
}: LeadBotSequenceProgressProps) {
  const [sequenceStatus, setSequenceStatus] = useState<SequenceStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { toast } = useToast();

  // Load sequence status
  useEffect(() => {
    loadSequenceStatus();

    // Refresh every 30 seconds
    const interval = setInterval(loadSequenceStatus, 30000);
    return () => clearInterval(interval);
  }, [leadId]);

  const loadSequenceStatus = async () => {
    try {
      const status = await leadBotApi.getSequenceStatus(leadId);
      setSequenceStatus(status);
      onSequenceUpdate?.(status);
    } catch (error) {
      console.error('Failed to load sequence status:', error);
      // Don't show error toast on initial load failure
      if (!loading) {
        toast({
          title: 'Failed to load sequence status',
          description: 'Please try refreshing the page',
          variant: 'destructive'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    if (!sequenceStatus) return;

    setActionLoading('pause');
    try {
      await leadBotApi.pauseSequence(leadId);
      await loadSequenceStatus();
      toast({
        title: 'Sequence paused',
        description: 'Lead sequence has been paused successfully'
      });
    } catch (error) {
      toast({
        title: 'Failed to pause sequence',
        description: 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleResume = async () => {
    if (!sequenceStatus) return;

    setActionLoading('resume');
    try {
      await leadBotApi.resumeSequence(leadId);
      await loadSequenceStatus();
      toast({
        title: 'Sequence resumed',
        description: 'Lead sequence has been resumed successfully'
      });
    } catch (error) {
      toast({
        title: 'Failed to resume sequence',
        description: 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancel = async () => {
    if (!sequenceStatus) return;

    setActionLoading('cancel');
    try {
      await leadBotApi.cancelSequence(leadId);
      await loadSequenceStatus();
      toast({
        title: 'Sequence cancelled',
        description: 'Lead sequence has been cancelled'
      });
    } catch (error) {
      toast({
        title: 'Failed to cancel sequence',
        description: 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Calculate progress percentage
  const calculateProgress = () => {
    if (!sequenceStatus?.progress) return 0;

    const { day_3_completed, day_7_completed, day_14_completed, day_30_completed } = sequenceStatus.progress;
    let completed = 0;
    if (day_3_completed) completed += 25;
    if (day_7_completed) completed += 25;
    if (day_14_completed) completed += 25;
    if (day_30_completed) completed += 25;

    return completed;
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'completed': return 'bg-blue-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  // Get sequence days data
  const getSequenceDays = () => {
    if (!sequenceStatus?.progress) return [];

    const { progress } = sequenceStatus;

    return [
      {
        day: 'DAY_3',
        label: 'Day 3',
        action: 'SMS',
        icon: MessageSquare,
        completed: progress.day_3_completed,
        deliveredAt: progress.day_3_delivered_at,
        isCurrent: sequenceStatus.current_day === 'DAY_3'
      },
      {
        day: 'DAY_7',
        label: 'Day 7',
        action: 'Voice Call',
        icon: Phone,
        completed: progress.day_7_completed,
        deliveredAt: progress.day_7_delivered_at,
        isCurrent: sequenceStatus.current_day === 'DAY_7'
      },
      {
        day: 'DAY_14',
        label: 'Day 14',
        action: 'Email',
        icon: Mail,
        completed: progress.day_14_completed,
        deliveredAt: progress.day_14_delivered_at,
        isCurrent: sequenceStatus.current_day === 'DAY_14'
      },
      {
        day: 'DAY_30',
        label: 'Day 30',
        action: 'Follow-up SMS',
        icon: MessageSquare,
        completed: progress.day_30_completed,
        deliveredAt: progress.day_30_delivered_at,
        isCurrent: sequenceStatus.current_day === 'DAY_30'
      }
    ];
  };

  if (loading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RotateCcw className="h-5 w-5 animate-spin" />
            Loading Sequence Status...
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  if (!sequenceStatus) {
    return (
      <Card className={cn('w-full border-dashed', className)}>
        <CardContent className="flex flex-col items-center justify-center py-8 text-center">
          <User className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No Active Sequence</h3>
          <p className="text-sm text-muted-foreground">
            No Lead Bot sequence found for this lead
          </p>
        </CardContent>
      </Card>
    );
  }

  const progress = calculateProgress();
  const sequenceDays = getSequenceDays();

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Lead Sequence Progress
          </CardTitle>
          <Badge variant="outline" className={cn('text-white', getStatusColor(sequenceStatus.status))}>
            {sequenceStatus.status.charAt(0).toUpperCase() + sequenceStatus.status.slice(1)}
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Overall Progress</span>
            <span>{progress}% Complete</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Sequence Timeline */}
        <div className="space-y-4">
          <h4 className="font-medium flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            30-Day Sequence Timeline
          </h4>

          <div className="space-y-3">
            {sequenceDays.map((day, index) => {
              const Icon = day.icon;

              return (
                <motion.div
                  key={day.day}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={cn(
                    'flex items-center gap-4 p-3 rounded-lg border',
                    day.isCurrent && 'border-primary bg-primary/5',
                    day.completed && 'bg-green-50 border-green-200'
                  )}
                >
                  <div className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-full',
                    day.completed ? 'bg-green-500 text-white' :
                    day.isCurrent ? 'bg-primary text-white' : 'bg-muted'
                  )}>
                    {day.completed ? <CheckCircle className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{day.label}</span>
                      <Badge variant="secondary" className="text-xs">
                        {day.action}
                      </Badge>
                      {day.isCurrent && (
                        <Badge variant="default" className="text-xs">
                          Current
                        </Badge>
                      )}
                    </div>

                    {day.deliveredAt && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Delivered: {new Date(day.deliveredAt).toLocaleString()}
                      </p>
                    )}

                    {day.isCurrent && sequenceStatus.next_action?.scheduled_for && (
                      <p className="text-xs text-primary mt-1">
                        Next: {new Date(sequenceStatus.next_action.scheduled_for).toLocaleString()}
                      </p>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        <Separator />

        {/* Engagement Metrics */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-1">
            <p className="text-muted-foreground">Response Count</p>
            <p className="font-semibold">{sequenceStatus.progress.response_count}</p>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">Engagement</p>
            <Badge variant="outline" className={cn(
              sequenceStatus.progress.engagement_status === 'high' && 'border-green-500 text-green-700',
              sequenceStatus.progress.engagement_status === 'medium' && 'border-yellow-500 text-yellow-700',
              sequenceStatus.progress.engagement_status === 'low' && 'border-red-500 text-red-700'
            )}>
              {sequenceStatus.progress.engagement_status}
            </Badge>
          </div>
        </div>

        {/* Next Action */}
        {sequenceStatus.next_action && (
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 text-sm font-medium text-blue-900">
              <Clock className="h-4 w-4" />
              Next Action
            </div>
            <p className="text-sm text-blue-800 mt-1">
              {sequenceStatus.next_action.action}
            </p>
            {sequenceStatus.next_action.scheduled_for && (
              <p className="text-xs text-blue-700 mt-1">
                Scheduled: {new Date(sequenceStatus.next_action.scheduled_for).toLocaleString()}
              </p>
            )}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex gap-2">
          <AnimatePresence mode="wait">
            {sequenceStatus.status === 'active' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex gap-2"
              >
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handlePause}
                  disabled={actionLoading === 'pause'}
                  className="flex items-center gap-2"
                >
                  <Pause className="h-4 w-4" />
                  {actionLoading === 'pause' ? 'Pausing...' : 'Pause'}
                </Button>

                <Button
                  size="sm"
                  variant="destructive"
                  onClick={handleCancel}
                  disabled={actionLoading === 'cancel'}
                  className="flex items-center gap-2"
                >
                  <Square className="h-4 w-4" />
                  {actionLoading === 'cancel' ? 'Cancelling...' : 'Cancel'}
                </Button>
              </motion.div>
            )}

            {sequenceStatus.status === 'paused' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex gap-2"
              >
                <Button
                  size="sm"
                  variant="default"
                  onClick={handleResume}
                  disabled={actionLoading === 'resume'}
                  className="flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  {actionLoading === 'resume' ? 'Resuming...' : 'Resume'}
                </Button>

                <Button
                  size="sm"
                  variant="destructive"
                  onClick={handleCancel}
                  disabled={actionLoading === 'cancel'}
                  className="flex items-center gap-2"
                >
                  <Square className="h-4 w-4" />
                  {actionLoading === 'cancel' ? 'Cancelling...' : 'Cancel'}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </CardContent>
    </Card>
  );
}