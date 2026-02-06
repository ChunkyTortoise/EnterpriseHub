# Frontend Platform Technical Specifications

## 🏗️ NEXT.JS PLATFORM ARCHITECTURE

**Mission**: Professional frontend that showcases existing production-ready bot ecosystem
**Stack**: Next.js 14 + TypeScript + Tailwind + Shadcn/ui

---

## 📁 PROJECT STRUCTURE

```
jorge-ai-platform/                     # New Next.js project
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── (dashboard)/               # Dashboard layout group
│   │   │   ├── concierge/             # Claude concierge interface
│   │   │   ├── bots/                  # Bot-specific interfaces
│   │   │   │   ├── seller/            # Jorge seller bot UI
│   │   │   │   ├── lead/              # Lead bot dashboard
│   │   │   │   └── analytics/         # ML analytics dashboard
│   │   │   ├── leads/                 # Lead management
│   │   │   ├── properties/            # Property matching
│   │   │   └── dashboard/             # Command center
│   │   ├── api/                       # API proxy routes
│   │   │   ├── bots/                  # Bot service proxies
│   │   │   ├── ghl/                   # GHL integration proxies
│   │   │   └── ws/                    # WebSocket endpoints
│   │   ├── globals.css                # Global styles
│   │   ├── layout.tsx                 # Root layout
│   │   └── page.tsx                   # Homepage
│   │
│   ├── components/                    # Reusable components
│   │   ├── ui/                        # Shadcn/ui components
│   │   ├── bots/                      # Bot-specific components
│   │   │   ├── JorgeSellerInterface/  # Seller bot chat UI
│   │   │   ├── LeadBotDashboard/      # Lead bot workflow UI
│   │   │   └── AnalyticsDashboard/    # ML insights UI
│   │   ├── concierge/                 # Concierge components
│   │   │   ├── ConciergeChat/         # AI guide interface
│   │   │   ├── WorkflowGuide/         # Step-by-step guidance
│   │   │   └── PlatformOverview/      # Status dashboard
│   │   ├── shared/                    # Shared UI components
│   │   │   ├── Header/                # Navigation header
│   │   │   ├── Sidebar/               # Navigation sidebar
│   │   │   └── StatusIndicators/      # Real-time status
│   │   └── mobile/                    # Mobile-optimized components
│   │
│   ├── hooks/                         # Custom React hooks
│   │   ├── useBots/                   # Bot service hooks
│   │   │   ├── useJorgeSellerBot.ts   # Jorge seller bot integration
│   │   │   ├── useLeadBot.ts          # Lead bot integration
│   │   │   └── useMLAnalytics.ts      # ML analytics integration
│   │   ├── useConcierge/              # Concierge hooks
│   │   │   ├── useConciergeContext.ts # Omnipresent awareness
│   │   │   └── useWorkflowGuide.ts    # Workflow guidance
│   │   └── useRealtime/               # Real-time updates
│   │       ├── useWebSocket.ts        # WebSocket connection
│   │       └── useLiveUpdates.ts      # Live data updates
│   │
│   ├── lib/                           # Utility libraries
│   │   ├── api/                       # API client functions
│   │   │   ├── bots.ts                # Bot service clients
│   │   │   ├── ghl.ts                 # GHL integration
│   │   │   └── websocket.ts           # WebSocket client
│   │   ├── stores/                    # State management
│   │   │   ├── platform.ts            # Global platform state
│   │   │   ├── bots.ts                # Bot session state
│   │   │   └── concierge.ts           # Concierge context
│   │   ├── utils.ts                   # Utility functions
│   │   └── types/                     # TypeScript types
│   │       ├── bots.ts                # Bot-related types
│   │       ├── platform.ts            # Platform types
│   │       └── api.ts                 # API response types
│   │
│   └── styles/                        # Styling
│       ├── globals.css                # Global styles
│       └── components.css             # Component styles
│
├── public/                            # Static assets
│   ├── icons/                         # App icons (PWA)
│   └── images/                        # Static images
│
├── .env.local                         # Environment variables
├── next.config.js                     # Next.js configuration
├── tailwind.config.js                 # Tailwind configuration
├── components.json                    # Shadcn/ui config
└── package.json                       # Dependencies
```

---

## 🛠️ TECHNOLOGY STACK

### **Core Framework**
```json
{
  "next": "^14.0.0",
  "react": "^18.0.0",
  "typescript": "^5.0.0"
}
```

### **Styling & UI**
```json
{
  "tailwindcss": "^3.3.0",
  "@tailwindcss/forms": "^0.5.0",
  "@tailwindcss/typography": "^0.5.0",
  "shadcn/ui": "latest",
  "lucide-react": "^0.400.0",
  "framer-motion": "^10.0.0"
}
```

### **State Management**
```json
{
  "zustand": "^4.4.0",
  "@tanstack/react-query": "^5.0.0",
  "swr": "^2.2.0"
}
```

### **Real-time & API**
```json
{
  "socket.io-client": "^4.7.0",
  "axios": "^1.6.0",
  "zod": "^3.22.0"
}
```

### **PWA & Mobile**
```json
{
  "next-pwa": "^5.6.0",
  "workbox-webpack-plugin": "^7.0.0"
}
```

### **Development & Testing**
```json
{
  "@playwright/test": "^1.40.0",
  "@testing-library/react": "^14.0.0",
  "jest": "^29.7.0",
  "eslint": "^8.0.0",
  "prettier": "^3.0.0"
}
```

---

## 🔗 API INTEGRATION LAYER

### **FastAPI Proxy Structure**
```typescript
// API Proxy Pattern
// src/app/api/bots/jorge-seller/route.ts

import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Proxy to existing FastAPI backend
    const response = await fetch(`${process.env.BACKEND_URL}/jorge-seller-bot`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.BACKEND_API_KEY}`,
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Bot service unavailable' },
      { status: 500 }
    )
  }
}
```

### **React Hook Integration**
```typescript
// src/hooks/useBots/useJorgeSellerBot.ts

import { useMutation } from '@tanstack/react-query'
import { jorgeSellerBotApi } from '@/lib/api/bots'

interface JorgeBotInput {
  leadId: string
  leadName: string
  conversationHistory: Array<{
    role: 'user' | 'assistant'
    content: string
    timestamp: string
  }>
}

interface JorgeBotResponse {
  response: string
  tone: 'direct' | 'confrontational' | 'take_away'
  temperature: 'hot' | 'warm' | 'cold'
  stallDetected: boolean
  detectedStallType?: 'thinking' | 'get_back' | 'zestimate' | 'agent'
  nextFollowUp?: string
  isQualified: boolean
  frs: number  // Financial Readiness Score
  pcs: number  // Psychological Commitment Score
}

export const useJorgeSellerBot = () => {
  return useMutation({
    mutationFn: (input: JorgeBotInput): Promise<JorgeBotResponse> =>
      jorgeSellerBotApi.processMessage(input),

    onSuccess: (data, variables) => {
      // Update concierge context with bot result
      useConciergeStore.getState().updateBotResult('jorge-seller', {
        leadId: variables.leadId,
        result: data,
        timestamp: new Date().toISOString(),
      })
    },

    onError: (error) => {
      console.error('Jorge Seller Bot error:', error)
      // Escalate to concierge for manual handling
    },
  })
}
```

---

## 🎯 COMPONENT SPECIFICATIONS

### **1. Concierge Chat Interface**
```typescript
// src/components/concierge/ConciergeChat/index.tsx

interface ConciergeMessage {
  id: string
  type: 'concierge' | 'user'
  content: string
  timestamp: string
  context?: {
    activeLeads: string[]
    suggestedActions: Array<{
      action: string
      description: string
      priority: 'high' | 'medium' | 'low'
    }>
    platformState: {
      botsActive: number
      pendingFollowups: number
      hotLeads: number
    }
  }
}

export const ConciergeChat = () => {
  const { messages, sendMessage, isTyping } = useConciergeChat()
  const { platformState } = usePlatformState()

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      <ConciergeHeader platformState={platformState} />
      <MessageList messages={messages} />
      {isTyping && <TypingIndicator />}
      <MessageInput onSend={sendMessage} />
    </div>
  )
}
```

### **2. Jorge Seller Bot Interface**
```typescript
// src/components/bots/JorgeSellerInterface/index.tsx

interface SellerBotProps {
  leadId: string
  leadName: string
  initialHistory?: ConversationMessage[]
}

export const JorgeSellerInterface = ({ leadId, leadName, initialHistory }: SellerBotProps) => {
  const { mutate: sendMessage, data: botResponse, isLoading } = useJorgeSellerBot()
  const [conversationHistory, setConversationHistory] = useState(initialHistory || [])

  const handleSendMessage = (message: string) => {
    const newMessage = {
      role: 'user' as const,
      content: message,
      timestamp: new Date().toISOString(),
    }

    setConversationHistory(prev => [...prev, newMessage])

    sendMessage({
      leadId,
      leadName,
      conversationHistory: [...conversationHistory, newMessage],
    })
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Conversation Interface */}
      <div className="lg:col-span-2">
        <ConversationWindow
          messages={conversationHistory}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>

      {/* Analytics Sidebar */}
      <div className="space-y-4">
        <ScoreCard
          title="Financial Readiness"
          score={botResponse?.frs || 0}
          description="Motivation and timeline assessment"
        />
        <ScoreCard
          title="Psychological Commitment"
          score={botResponse?.pcs || 0}
          description="Conversation engagement level"
        />
        <TemperatureIndicator
          temperature={botResponse?.temperature}
          tone={botResponse?.tone}
        />
        {botResponse?.stallDetected && (
          <StallAlert stallType={botResponse.detectedStallType} />
        )}
      </div>
    </div>
  )
}
```

### **3. Lead Bot Dashboard**
```typescript
// src/components/bots/LeadBotDashboard/index.tsx

interface LeadBotDashboardProps {
  leadId: string
}

export const LeadBotDashboard = ({ leadId }: LeadBotDashboardProps) => {
  const { data: leadData } = useLeadBotData(leadId)
  const { mutate: triggerFollowup } = useLeadBotFollowup()

  return (
    <div className="space-y-6">
      {/* Progress Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Lead Journey Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <Timeline
            stages={[
              { name: 'Initial Contact', status: leadData?.stages.initial, date: leadData?.dates.initial },
              { name: 'Day 3 SMS', status: leadData?.stages.day3, date: leadData?.dates.day3 },
              { name: 'Day 7 Call', status: leadData?.stages.day7, date: leadData?.dates.day7 },
              { name: 'Day 14 CMA', status: leadData?.stages.day14, date: leadData?.dates.day14 },
              { name: 'Day 30 Nudge', status: leadData?.stages.day30, date: leadData?.dates.day30 },
            ]}
          />
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Available Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <Button
              onClick={() => triggerFollowup({ leadId, type: 'sms' })}
              disabled={!leadData?.canSendSMS}
            >
              Send SMS Follow-up
            </Button>
            <Button
              onClick={() => triggerFollowup({ leadId, type: 'call' })}
              disabled={!leadData?.canCall}
            >
              Schedule Retell Call
            </Button>
            <Button
              onClick={() => triggerFollowup({ leadId, type: 'cma' })}
              disabled={!leadData?.canSendCMA}
            >
              Generate CMA
            </Button>
            <Button
              onClick={() => triggerFollowup({ leadId, type: 'nurture' })}
              disabled={!leadData?.canNurture}
            >
              Send Nurture Email
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analytics */}
      <EngagementAnalytics leadId={leadId} />
    </div>
  )
}
```

---

## 🔄 STATE MANAGEMENT

### **Global Platform State (Zustand)**
```typescript
// src/lib/stores/platform.ts

interface PlatformState {
  // Current session
  activeLeads: Lead[]
  botSessions: BotSession[]

  // Real-time updates
  liveUpdates: LiveUpdate[]

  // Concierge context
  conciergeHistory: ConciergeMessage[]
  suggestedActions: SuggestedAction[]

  // Platform status
  botsStatus: Record<string, 'active' | 'idle' | 'error'>
  ghlConnection: 'connected' | 'disconnected' | 'error'

  // Actions
  updateActiveLeads: (leads: Lead[]) => void
  addBotSession: (session: BotSession) => void
  updateBotStatus: (botId: string, status: BotStatus) => void
  addConciergeMessage: (message: ConciergeMessage) => void
}

export const usePlatformStore = create<PlatformState>((set, get) => ({
  // Initial state
  activeLeads: [],
  botSessions: [],
  liveUpdates: [],
  conciergeHistory: [],
  suggestedActions: [],
  botsStatus: {},
  ghlConnection: 'disconnected',

  // Actions
  updateActiveLeads: (leads) => set({ activeLeads: leads }),

  addBotSession: (session) => set((state) => ({
    botSessions: [...state.botSessions, session],
  })),

  updateBotStatus: (botId, status) => set((state) => ({
    botsStatus: { ...state.botsStatus, [botId]: status },
  })),

  addConciergeMessage: (message) => set((state) => ({
    conciergeHistory: [...state.conciergeHistory, message],
  })),
}))
```

### **Real-time Updates (WebSocket)**
```typescript
// src/hooks/useRealtime/useWebSocket.ts

export const useWebSocket = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const updatePlatformState = usePlatformStore((state) => state.updatePlatformState)

  useEffect(() => {
    const newSocket = io(process.env.NEXT_PUBLIC_WEBSOCKET_URL!, {
      transports: ['websocket'],
    })

    // Bot completion events
    newSocket.on('bot_completed', (data: BotCompletionEvent) => {
      updatePlatformState({
        type: 'bot_completed',
        botId: data.botId,
        result: data.result,
        timestamp: data.timestamp,
      })
    })

    // New lead events
    newSocket.on('lead_updated', (data: LeadUpdateEvent) => {
      updatePlatformState({
        type: 'lead_updated',
        leadId: data.leadId,
        changes: data.changes,
        timestamp: data.timestamp,
      })
    })

    // GHL webhook events
    newSocket.on('ghl_webhook', (data: GHLWebhookEvent) => {
      updatePlatformState({
        type: 'ghl_webhook',
        eventType: data.eventType,
        data: data.data,
        timestamp: data.timestamp,
      })
    })

    setSocket(newSocket)

    return () => {
      newSocket.disconnect()
    }
  }, [updatePlatformState])

  return socket
}
```

---

## 📱 MOBILE OPTIMIZATION

### **Progressive Web App Configuration**
```javascript
// next.config.js

const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/api\./i,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        networkTimeoutSeconds: 10,
        expiration: {
          maxEntries: 32,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        },
      },
    },
  ],
})

module.exports = withPWA({
  // Next.js config
  experimental: {
    appDir: true,
  },

  // PWA specific
  pwa: {
    dest: 'public',
    register: true,
    skipWaiting: true,
  },
})
```

### **Mobile-First Responsive Design**
```css
/* src/styles/globals.css */

/* Mobile-first approach */
@media (min-width: 640px) {
  /* sm: Small screens (640px and up) */
}

@media (min-width: 768px) {
  /* md: Medium screens (768px and up) */
}

@media (min-width: 1024px) {
  /* lg: Large screens (1024px and up) */
}

@media (min-width: 1280px) {
  /* xl: Extra large screens (1280px and up) */
}

/* Touch-friendly button sizes */
.touch-target {
  min-height: 44px;
  min-width: 44px;
}

/* Mobile-optimized typography */
@screen sm {
  .text-responsive {
    font-size: 1rem;
  }
}

@screen lg {
  .text-responsive {
    font-size: 1.125rem;
  }
}
```

---

## ⚡ PERFORMANCE OPTIMIZATION

### **React Query Configuration**
```typescript
// src/lib/queryClient.ts

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && error.message.includes('4')) {
          return false
        }
        return failureCount < 3
      },
    },
    mutations: {
      retry: 1,
    },
  },
})
```

### **Code Splitting Strategy**
```typescript
// Dynamic imports for heavy components
const JorgeSellerInterface = dynamic(
  () => import('@/components/bots/JorgeSellerInterface'),
  {
    loading: () => <BotLoadingSkeleton />,
    ssr: false, // Don't server-render heavy interactive components
  }
)

const MLAnalyticsDashboard = dynamic(
  () => import('@/components/bots/AnalyticsDashboard'),
  {
    loading: () => <AnalyticsLoadingSkeleton />,
  }
)
```

---

## 🧪 TESTING STRATEGY

### **E2E Testing with Playwright**
```typescript
// tests/e2e/jorge-seller-bot.spec.ts

import { test, expect } from '@playwright/test'

test.describe('Jorge Seller Bot Interface', () => {
  test('should qualify a hot lead correctly', async ({ page }) => {
    // Navigate to bot interface
    await page.goto('/bots/seller')

    // Start conversation
    await page.fill('[data-testid="message-input"]', 'I need to sell my house ASAP')
    await page.click('[data-testid="send-button"]')

    // Wait for bot response
    await expect(page.locator('[data-testid="bot-response"]')).toBeVisible()

    // Check FRS/PCS scores update
    await expect(page.locator('[data-testid="frs-score"]')).toContainText(/[5-9]\d/)
    await expect(page.locator('[data-testid="temperature"]')).toContainText('Hot')

    // Continue conversation to qualification
    await page.fill('[data-testid="message-input"]', 'Within 30 days, as-is condition')
    await page.click('[data-testid="send-button"]')

    // Should show qualified status
    await expect(page.locator('[data-testid="qualification-status"]')).toContainText('Qualified')

    // Should trigger GHL workflow
    await expect(page.locator('[data-testid="ghl-status"]')).toContainText('Workflow Triggered')
  })
})
```

---

## 🚀 DEPLOYMENT CONFIGURATION

### **Environment Variables**
```bash
# .env.local

# Backend Integration
BACKEND_URL=http://localhost:8000
BACKEND_API_KEY=your_backend_api_key

# WebSocket
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000/ws

# External Services
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Analytics
NEXT_PUBLIC_POSTHOG_KEY=your_posthog_key
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# Production
NEXT_PUBLIC_APP_URL=https://jorge-ai-platform.com
```

### **Docker Configuration**
```dockerfile
# Dockerfile

FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

---

## 🎯 SUCCESS METRICS

### **Performance Targets**
- [ ] **First Contentful Paint**: < 1.5s
- [ ] **Largest Contentful Paint**: < 2.5s
- [ ] **Time to Interactive**: < 3.0s
- [ ] **Cumulative Layout Shift**: < 0.1
- [ ] **Bot Response Display**: < 100ms after API response

### **Mobile Targets**
- [ ] **Mobile PageSpeed Score**: > 90
- [ ] **Touch Target Size**: Min 44px x 44px
- [ ] **Viewport Optimization**: Works on 320px+ widths
- [ ] **Offline Functionality**: Core features work offline
- [ ] **PWA Installation**: One-click installation from browser

### **User Experience Targets**
- [ ] **Bot Interface**: Feels like messaging a human expert
- [ ] **Concierge Guidance**: Provides helpful proactive suggestions
- [ ] **Mobile Workflow**: Complete workflows possible on mobile
- [ ] **Professional Polish**: Inspires client confidence
- [ ] **Real-time Updates**: Live coordination between bots

---

## 🏆 FINAL DELIVERABLE CHECKLIST

### **Core Platform** ✅
- [ ] Next.js 14 project with TypeScript
- [ ] Professional component library (Shadcn/ui)
- [ ] API proxy layer to existing backend
- [ ] Real-time WebSocket integration
- [ ] Global state management (Zustand + React Query)

### **Bot Interfaces** ✅
- [ ] Jorge Seller Bot professional chat UI
- [ ] Lead Bot dashboard with 3-7-30 timeline
- [ ] ML Analytics dashboard with SHAP explanations
- [ ] Real-time scoring and status updates
- [ ] GHL integration status indicators

### **Concierge Intelligence** ✅
- [ ] Omnipresent chat interface
- [ ] Platform state awareness
- [ ] Workflow guidance and routing
- [ ] Proactive suggestion engine
- [ ] Context persistence across sessions

### **Mobile Experience** ✅
- [ ] Progressive Web App capabilities
- [ ] Mobile-optimized touch interfaces
- [ ] Offline functionality for core features
- [ ] Field agent workflow optimization
- [ ] Performance optimized for mobile networks

### **Quality Assurance** ✅
- [ ] E2E test suite (Playwright)
- [ ] Unit tests for critical components
- [ ] Performance monitoring (Core Web Vitals)
- [ ] Accessibility compliance (WCAG 2.1 AA)
- [ ] Cross-browser compatibility

**Mission Accomplished**: Professional platform that showcases Jorge's production-ready bot ecosystem with enterprise-grade polish and mobile excellence! 🏠✨