/**
 * Lead Bot Message Timeline Component
 *
 * Displays chronological timeline of Lead Bot sequence actions
 * Shows messages sent, calls made, and lead responses
 */

'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  MessageSquare,
  Phone,
  Mail,
  CheckCircle,
  AlertCircle,
  Clock,
  User,
  Bot,
  TrendingUp,
  Volume2,
  ExternalLink,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useAgentEcosystemStore } from '@/store/agentEcosystemStore';

interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'sequence_progress' | 'action_success' | 'action_error' | 'lead_response' | 'state_change';
  message: string;
  data?: {
    leadId?: string;
    actionType?: 'sms' | 'call' | 'email';
    sequenceDay?: 'DAY_3' | 'DAY_7' | 'DAY_14' | 'DAY_30';
    duration?: number;
    engagementScore?: number;
    content?: string;
    sentiment?: 'positive' | 'negative' | 'neutral';
    error?: string;
    responseMethod?: 'sms' | 'call_answer' | 'email_reply';
  };
}

interface LeadBotMessageTimelineProps {
  leadId: string;
  className?: string;
  maxEvents?: number;
}

export function LeadBotMessageTimeline({
  leadId,
  className,
  maxEvents = 20
}: LeadBotMessageTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  // Get events from agent ecosystem store
  const { bots } = useAgentEcosystemStore();
  const leadBotEvents = bots['lead-bot']?.events || [];

  useEffect(() => {
    // Filter and format events for this lead
    const leadEvents = leadBotEvents
      .filter((event) => event.data?.leadId === leadId)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, maxEvents)
      .map((event) => ({
        id: `${event.timestamp}-${event.type}`,
        timestamp: event.timestamp,
        type: event.type as TimelineEvent['type'],
        message: event.message,
        data: event.data as TimelineEvent['data']
      }));

    setEvents(leadEvents);
    setLoading(false);
  }, [leadBotEvents, leadId, maxEvents]);

  // Get icon for event type
  const getEventIcon = (event: TimelineEvent) => {
    switch (event.type) {
      case 'sequence_progress':
        return Clock;
      case 'action_success':
        if (event.data?.actionType === 'sms') return MessageSquare;
        if (event.data?.actionType === 'call') return Phone;
        if (event.data?.actionType === 'email') return Mail;
        return CheckCircle;
      case 'action_error':
        return AlertCircle;
      case 'lead_response':
        return User;
      case 'state_change':
        return TrendingUp;
      default:
        return Bot;
    }
  };

  // Get event color
  const getEventColor = (event: TimelineEvent) => {
    switch (event.type) {
      case 'sequence_progress':
        return 'text-blue-600 bg-blue-100';
      case 'action_success':
        return 'text-green-600 bg-green-100';
      case 'action_error':
        return 'text-red-600 bg-red-100';
      case 'lead_response':
        return 'text-purple-600 bg-purple-100';
      case 'state_change':
        return 'text-orange-600 bg-orange-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Format relative time
  const formatRelativeTime = (timestamp: string) => {
    const now = new Date();
    const eventTime = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - eventTime.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;

    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;

    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  // Render event details
  const renderEventDetails = (event: TimelineEvent) => {
    switch (event.type) {
      case 'action_success':
        return (
          <div className="mt-2 text-sm">
            {event.data?.actionType && (
              <Badge variant="secondary" className="mr-2">
                {event.data.actionType.toUpperCase()}
              </Badge>
            )}
            {event.data?.sequenceDay && (
              <Badge variant="outline" className="mr-2">
                {event.data.sequenceDay.replace('DAY_', 'Day ')}
              </Badge>
            )}
            {event.data?.duration && (
              <span className="text-muted-foreground">
                Duration: {event.data.duration}s
              </span>
            )}
            {event.data?.engagementScore && (
              <div className="mt-1">
                <span className="text-muted-foreground">Engagement: </span>
                <Badge variant={event.data.engagementScore > 0.7 ? 'default' :
                               event.data.engagementScore > 0.4 ? 'secondary' : 'outline'}>
                  {Math.round(event.data.engagementScore * 100)}%
                </Badge>
              </div>
            )}
          </div>
        );

      case 'action_error':
        return (
          <div className="mt-2">
            {event.data?.error && (
              <p className="text-sm text-red-600 bg-red-50 p-2 rounded">
                {event.data.error}
              </p>
            )}
          </div>
        );

      case 'lead_response':
        return (
          <div className="mt-2 space-y-2">
            <div className="flex items-center gap-2">
              {event.data?.responseMethod && (
                <Badge variant="secondary">
                  {event.data.responseMethod === 'sms' ? 'SMS' :
                   event.data.responseMethod === 'call_answer' ? 'Call Answered' :
                   'Email Reply'}
                </Badge>
              )}
              {event.data?.sentiment && (
                <Badge variant={event.data.sentiment === 'positive' ? 'default' :
                               event.data.sentiment === 'negative' ? 'destructive' : 'secondary'}>
                  {event.data.sentiment}
                </Badge>
              )}
            </div>
            {event.data?.content && (
              <p className="text-sm bg-purple-50 p-2 rounded italic">
                "{event.data.content.length > 100
                  ? event.data.content.substring(0, 100) + '...'
                  : event.data.content}"
              </p>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 animate-spin" />
            Loading Timeline...
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Message Timeline
          </div>
          <Badge variant="outline">
            {events.length} events
          </Badge>
        </CardTitle>
      </CardHeader>

      <CardContent>
        {events.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No timeline events yet</p>
            <p className="text-sm">Lead Bot actions will appear here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {events.map((event, index) => {
              const Icon = getEventIcon(event);
              const colorClass = getEventColor(event);

              return (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="relative flex gap-4"
                >
                  {/* Timeline Line */}
                  {index < events.length - 1 && (
                    <div className="absolute left-6 top-12 h-full w-px bg-border" />
                  )}

                  {/* Event Icon */}
                  <div className={cn(
                    'flex h-12 w-12 items-center justify-center rounded-full border-2 border-background',
                    colorClass
                  )}>
                    <Icon className="h-5 w-5" />
                  </div>

                  {/* Event Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{event.message}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatRelativeTime(event.timestamp)} • {new Date(event.timestamp).toLocaleString()}
                        </p>
                      </div>

                      {/* Lead Response Indicator */}
                      {event.type === 'lead_response' && (
                        <Avatar className="h-8 w-8 ml-2">
                          <AvatarFallback className="bg-purple-100 text-purple-600">
                            <User className="h-4 w-4" />
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </div>

                    {/* Event Details */}
                    {renderEventDetails(event)}
                  </div>
                </motion.div>
              );
            })}

            {events.length >= maxEvents && (
              <>
                <Separator />
                <div className="text-center text-sm text-muted-foreground">
                  Showing last {maxEvents} events
                </div>
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}