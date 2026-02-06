# Phase 6: Frontend Integration & WebSocket Infrastructure - Continuation Prompt

**Status**: 65-70% complete - frontend is production-ready but backend connections are the main blocker
**Critical Issue**: 10 TODO API endpoints return mock data instead of connecting to FastAPI backend
**Time to Complete**: 23-32 hours

## 🎯 IMMEDIATE OBJECTIVE
Connect the production-ready React frontend to the FastAPI backend. All UI components, state management, and WebSocket infrastructure are complete, but API routes return mock data instead of proxying to the actual backend services.

## 📁 KEY FILES TO FOCUS ON

### Primary Files (MUST IMPLEMENT):
- `enterprise-ui/src/app/api/bots/jorge-seller/route.ts` - **TODO**: Replace mock with FastAPI calls
- `enterprise-ui/src/app/api/bots/lead-bot/route.ts` - **TODO**: Connect to lead automation API
- `enterprise-ui/src/app/api/dashboard/metrics/route.ts` - **TODO**: Connect to real metrics
- `enterprise-ui/src/app/api/concierge/chat/route.ts` - **TODO**: Add Redis rate limiting
- `enterprise-ui/src/components/providers/WebSocketProvider.tsx` - **TODO**: Configure backend URL

### Files to Read for Context:
- `enterprise-ui/src/components/JorgeCommandCenter.tsx` - Complete UI (ready)
- `enterprise-ui/src/components/claude-concierge/ClaudeConcierge.tsx` - Complete UI (ready)
- `enterprise-ui/src/lib/claude-concierge/ClaudeConciergeService.ts` - Complete service (1,425 lines)
- `enterprise-ui/src/store/useConciergeStore.ts` - Complete state management

## 🚨 CRITICAL BLOCKING ISSUES

### 1. **BACKEND API INTEGRATION** (Priority: CRITICAL)
**Problem**: 10 API routes have TODO comments for FastAPI backend integration

**Route Files with TODOs:**
```typescript
// enterprise-ui/src/app/api/bots/jorge-seller/route.ts (lines 48, 111)
TODO: Replace with actual FastAPI backend call
TODO: Get seller state from FastAPI backend

// enterprise-ui/src/app/api/bots/lead-bot/route.ts (lines 48, 131)
TODO: Replace with actual FastAPI backend call
TODO: Get automation status from FastAPI backend

// enterprise-ui/src/app/api/dashboard/metrics/route.ts (line 93)
TODO: Replace with actual FastAPI backend call

// enterprise-ui/src/app/api/leads/intelligence/route.ts (lines 75, 185)
TODO: Replace with actual FastAPI backend call to ML analytics
TODO: Get analysis history from FastAPI backend

// enterprise-ui/src/app/api/concierge/chat/route.ts (line 66)
TODO: Implement proper rate limiting with Redis
```

**Impact**: Currently returns mock data. Frontend works perfectly but with fake data.

### 2. **WEBSOCKET BACKEND CONNECTION** (Priority: CRITICAL)
**File**: `enterprise-ui/src/components/providers/WebSocketProvider.tsx`
**Problem**: No backend WebSocket URL configured

```typescript
// Current:
const socket = io(); // ← CONNECTS TO NOTHING

// Needed:
const socket = io(process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:8000', {
  path: '/socket.io',
  transports: ['websocket']
});
```

**Missing environment variables:**
- `NEXT_PUBLIC_WEBSOCKET_URL`
- `NEXT_PUBLIC_API_BASE`

### 3. **OMNIPRESENT COORDINATION EVENTS** (Priority: HIGH)
**Problem**: UI handles coordination events but backend doesn't emit them

**Missing backend event emissions:**
```python
# Backend needs to emit these events:
socket_manager.emit('bot_handoff_request', {
    'from_bot': 'claude_concierge',
    'to_bot': 'jorge_seller_bot',
    'context': conversation_context
})

socket_manager.emit('coaching_opportunity', {
    'opportunity_type': 'objection_handling',
    'suggestion': 'Ask about timeline urgency'
})

socket_manager.emit('context_sync_event', {
    'bot_id': 'jorge_seller_bot',
    'context_update': updated_context
})
```

**Frontend is ready to receive these events, backend doesn't send them.**

## ⚡ PRIORITY 1: BACKEND INTEGRATION (CRITICAL - 8-12 hours)

### 1. **Connect Jorge Seller Bot API** (2-3 hours)
**File**: `enterprise-ui/src/app/api/bots/jorge-seller/route.ts`
**Replace mock responses with FastAPI calls:**

```typescript
// BEFORE (line 48):
// TODO: Replace with actual FastAPI backend call
return NextResponse.json({
  id: "mock-conversation",
  // ... mock data
});

// AFTER:
const response = await fetch(`${process.env.BACKEND_URL}/api/bots/jorge-seller/chat`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${process.env.BACKEND_API_KEY}`
  },
  body: JSON.stringify({
    message: message,
    lead_context: context
  })
});

if (!response.ok) {
  throw new Error(`Backend API error: ${response.status}`);
}

const data = await response.json();
return NextResponse.json(data);
```

### 2. **Connect Lead Bot Automation API** (2-3 hours)
**File**: `enterprise-ui/src/app/api/bots/lead-bot/route.ts`
**Connect to 3-7-30 day automation system:**

```typescript
// Connect to FastAPI endpoints:
// POST /api/bots/lead-bot/automation/start
// GET /api/bots/lead-bot/automation/{lead_id}/status
// POST /api/bots/lead-bot/automation/{lead_id}/schedule
```

### 3. **Connect Dashboard Metrics API** (2-3 hours)
**File**: `enterprise-ui/src/app/api/dashboard/metrics/route.ts`
**Connect to real-time metrics from Jorge ecosystem:**

```typescript
// Connect to FastAPI endpoints:
// GET /api/metrics/dashboard/real-time
// GET /api/metrics/bots/performance
// GET /api/metrics/ml/scoring-stats
```

### 4. **Configure WebSocket URL** (1 hour)
**File**: `enterprise-ui/.env.local` (CREATE)
```bash
NEXT_PUBLIC_WEBSOCKET_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE=http://localhost:8000
BACKEND_URL=http://localhost:8000
BACKEND_API_KEY=your_api_key_here
```

**File**: `enterprise-ui/src/components/providers/WebSocketProvider.tsx`
```typescript
const socket = io(process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:8000');
```

## ⚡ PRIORITY 2: OMNIPRESENT COORDINATION (HIGH - 6-8 hours)

### 1. **Wire Bot Coordination Events** (4-5 hours)
**Backend**: Emit coordination events from Jorge bot ecosystem
```python
# In jorge_seller_bot.py
await socket_manager.emit('bot_handoff_request', {
    'from_bot': 'claude_concierge',
    'to_bot': 'jorge_seller_bot',
    'lead_id': lead_id,
    'context': current_context
})

# In ML scoring pipeline
await socket_manager.emit('coaching_opportunity', {
    'type': 'ml_insight',
    'suggestion': 'Lead shows high buying intent - suggest urgency questions'
})
```

### 2. **Test Handoff Flow End-to-End** (2-3 hours)
Validate: Concierge → Jorge Seller Bot handoff with context preservation
Test: Real-time coaching suggestions appear in UI
Verify: Bot status updates reflect in command center

## ⚡ PRIORITY 3: RATE LIMITING & SECURITY (MEDIUM - 3-4 hours)

### 1. **Implement Redis Rate Limiting** (2-3 hours)
**File**: `enterprise-ui/src/app/api/concierge/chat/route.ts`
```typescript
import { redis } from '@/lib/redis';

// Implement rate limiting before processing chat
const clientId = headers.get('x-forwarded-for') || 'unknown';
const rateLimitKey = `concierge_chat:${clientId}`;
const requestCount = await redis.incr(rateLimitKey);

if (requestCount === 1) {
  await redis.expire(rateLimitKey, 60); // 1 minute window
}

if (requestCount > 10) {
  return NextResponse.json(
    { error: 'Rate limit exceeded' },
    { status: 429 }
  );
}
```

### 2. **Add Request Validation** (1 hour)
Validate API keys for backend requests
Add CORS headers for cross-origin requests
Implement request logging for debugging

## 💡 SUCCESS CRITERIA

**Phase 6 Complete When:**
- [ ] All 10 TODO API endpoints connect to actual FastAPI backend
- [ ] WebSocket connection established and receiving real-time events
- [ ] Jorge Seller Bot conversation works end-to-end
- [ ] Lead Bot automation status displays real data
- [ ] Dashboard metrics show actual Jorge ecosystem performance
- [ ] Concierge → Bot handoff works with context preservation
- [ ] Rate limiting protects against API abuse
- [ ] Real-time coaching suggestions appear based on ML insights

## 🧪 TESTING COMMANDS

```bash
# Ensure FastAPI backend is running
cd ghl_real_estate_ai
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Start Next.js frontend
cd enterprise-ui
npm run dev

# Test API proxy connections
curl http://localhost:3000/api/bots/jorge-seller \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I want to sell my house", "context": {}}'

# Test WebSocket connection
node -e "
const io = require('socket.io-client');
const socket = io('http://localhost:3000');
socket.on('connect', () => console.log('Connected to Next.js WebSocket proxy'));
socket.on('bot_status_update', (data) => console.log('Bot status:', data));
"

# Test real-time metrics
curl http://localhost:3000/api/dashboard/metrics
```

## 📊 WHAT'S ALREADY COMPLETE AND PERFECT

✅ **JorgeCommandCenter** - Complete dashboard with bot performance cards
✅ **ClaudeConcierge** - Full omnipresent AI assistant (1,425 lines)
✅ **WebSocket Infrastructure** - Connection management, auto-reconnection
✅ **State Management** - Comprehensive Zustand store with persistence
✅ **Real-time Hooks** - useBotStatus, useRealTimeMetrics
✅ **UI Components** - Professional interface ready for production
✅ **Mobile Support** - PWA with location-based features
✅ **TypeScript Integration** - Full type safety across codebase

## 🚫 WHAT NOT TO REBUILD

**DON'T rewrite the frontend components** - they're production-ready. Focus on:
1. **API Integration** - Connect TODO endpoints to backend
2. **WebSocket Configuration** - Set backend URL and test connection
3. **Event Wiring** - Ensure backend emits coordination events
4. **Rate Limiting** - Add Redis-based protection
5. **Testing** - Validate end-to-end data flow

## 🎯 IMPLEMENTATION PATTERNS

**For API proxy endpoints, follow this pattern:**
```typescript
export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Validate input
    if (!body.message) {
      return NextResponse.json({ error: 'Message required' }, { status: 400 });
    }

    // Proxy to FastAPI backend
    const response = await fetch(`${process.env.BACKEND_URL}/api/...`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.BACKEND_API_KEY}`
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${error}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**Phase 6 is UI-complete and just needs backend wiring. Focus on data flow, not rebuilding components.**