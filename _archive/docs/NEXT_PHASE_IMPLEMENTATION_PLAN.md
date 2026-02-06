# Jorge's Next.js Migration Implementation Plan
*Based on Perplexity research evaluation - January 2026*

## Phase 1: Foundation Setup (Week 1-2)

### Day 1-3: Next.js 14 Project Initialization
```bash
# Create Next.js 14 project with research recommendations
npx create-next-app@latest jorge-enterprise-platform \
  --typescript --tailwind --eslint --app --src-dir

cd jorge-enterprise-platform

# Install core dependencies from research
npm install \
  @supabase/supabase-js \
  zustand \
  @tanstack/react-query \
  next-auth \
  socket.io-client

# Install UI components (research priority)
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input form dialog
```

### Day 4-5: Connect to Existing Backend
```typescript
// lib/api-client.ts - Connect to our FastAPI backend
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export const apiClient = {
  async getBotStatus(botId: string) {
    const response = await fetch(`${API_BASE}/bots/${botId}/status`)
    return response.json()
  },
  
  async sendMessage(botId: string, message: string) {
    const response = await fetch(`${API_BASE}/bots/${botId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    })
    return response.json()
  }
}
```

## Phase 2: Core Bot Interface (Week 3-4)

### Bot Dashboard Component
```typescript
// components/jorge-command-center.tsx
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function JorgeCommandCenter() {
  const { data: bots } = useQuery({
    queryKey: ['bots'],
    queryFn: () => apiClient.getBots()
  })
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {bots?.map(bot => (
        <Card key={bot.id}>
          <CardHeader>
            <CardTitle>{bot.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                bot.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
              }`} />
              <span>{bot.status}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
```

### Real-time Chat Interface
```typescript
// components/chat-interface.tsx
import { useEffect, useState } from 'react'
import { useChatStore } from '@/stores/chat-store'
import { io } from 'socket.io-client'

export function ChatInterface({ botId }: { botId: string }) {
  const { messages, addMessage } = useChatStore()
  const [socket, setSocket] = useState(null)
  
  useEffect(() => {
    const newSocket = io(process.env.NEXT_PUBLIC_SOCKET_URL)
    newSocket.on('message', addMessage)
    setSocket(newSocket)
    
    return () => newSocket.close()
  }, [])
  
  return (
    <div className="flex flex-col h-96">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map(msg => (
          <div key={msg.id} className={`mb-2 ${
            msg.role === 'user' ? 'text-right' : 'text-left'
          }`}>
            <div className={`inline-block p-2 rounded-lg ${
              msg.role === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-black'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>
      <ChatInput onSend={(msg) => socket?.emit('message', { content: msg, botId })} />
    </div>
  )
}
```

## Phase 3: Property Integration (Week 5-6)

### Enhanced Property Cards
```typescript
// components/property-card.tsx - Based on research recommendations
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Heart, MapPin, Bed, Bath } from 'lucide-react'

interface PropertyCardProps {
  id: string
  address: string
  price: number
  beds: number
  baths: number
  imageUrl: string
  matchScore?: number // Jorge's ML scoring integration
}

export function PropertyCard({ property }: { property: PropertyCardProps }) {
  const { data: aiInsights } = useQuery({
    queryKey: ['property-insights', property.id],
    queryFn: () => apiClient.getPropertyAIInsights(property.id)
  })
  
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="relative">
        <img src={property.imageUrl} alt={property.address} 
             className="w-full h-48 object-cover rounded-t-lg" />
        
        {property.matchScore && (
          <div className="absolute top-2 left-2 bg-green-500 text-white px-2 py-1 rounded">
            {property.matchScore}% Match
          </div>
        )}
      </div>
      
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-semibold">${property.price.toLocaleString()}</h3>
          <Button variant="ghost" size="sm">
            <Heart className="w-4 h-4" />
          </Button>
        </div>
        
        <p className="text-sm text-gray-600 mb-2">{property.address}</p>
        
        <div className="flex gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Bed className="w-4 h-4" />
            {property.beds} bed
          </span>
          <span className="flex items-center gap-1">
            <Bath className="w-4 h-4" />
            {property.baths} bath
          </span>
        </div>
        
        {aiInsights && (
          <div className="mt-3 p-2 bg-blue-50 rounded text-sm">
            <strong>Jorge's AI:</strong> {aiInsights.summary}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

## Phase 4: PWA & Mobile (Week 7-8)

### PWA Configuration
```javascript
// next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development'
})

module.exports = withPWA({
  experimental: {
    appDir: true
  }
})
```

### Offline Capabilities
```typescript
// hooks/use-offline-sync.ts
export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(true)
  
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])
  
  const syncOfflineData = async () => {
    if (isOnline) {
      const offlineActions = getOfflineQueue()
      for (const action of offlineActions) {
        await apiClient.syncAction(action)
      }
      clearOfflineQueue()
    }
  }
  
  return { isOnline, syncOfflineData }
}
```

## Integration with Existing Jorge Backend

### FastAPI Route Enhancements
```python
# Add to existing ghl_real_estate_ai/api/routes/
@router.get("/api/bots/{bot_id}/status")
async def get_bot_status(bot_id: str):
    """New endpoint for Next.js frontend"""
    bot = get_bot_by_id(bot_id)
    return {
        "id": bot_id,
        "name": bot.name,
        "status": "online" if bot.is_active() else "offline",
        "last_activity": bot.last_activity,
        "response_time_ms": bot.avg_response_time
    }

@router.post("/api/bots/{bot_id}/chat")
async def chat_with_bot(bot_id: str, message: ChatMessage):
    """Enhanced chat endpoint with streaming"""
    bot = get_bot_by_id(bot_id)
    
    async def generate_response():
        async for chunk in bot.stream_response(message.content):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
    
    return StreamingResponse(generate_response(), media_type="text/plain")
```

## Testing Strategy

### Component Testing with Playwright
```typescript
// e2e/jorge-bot-interaction.spec.ts
import { test, expect } from '@playwright/test'

test('Jorge Seller Bot conversation flow', async ({ page }) => {
  await page.goto('/bots/jorge-seller')
  
  // Verify bot loads
  await expect(page.locator('[data-testid="bot-status"]')).toContainText('Ready')
  
  // Send qualification message
  await page.fill('[data-testid="chat-input"]', 'I want to sell my house')
  await page.click('[data-testid="send-button"]')
  
  // Verify confrontational qualification starts
  await expect(page.locator('.bot-message:last-child')).toContainText(
    'financial readiness', { timeout: 10000 }
  )
  
  // Verify GHL integration
  await expect(page.locator('[data-testid="lead-status"]')).toContainText('Synced')
})
```

## Deployment Configuration

### Vercel Deployment
```javascript
// vercel.json
{
  "framework": "nextjs",
  "functions": {
    "app/api/chat/route.ts": {
      "maxDuration": 30
    }
  },
  "env": {
    "NEXT_PUBLIC_API_BASE": "https://your-backend.railway.app",
    "SUPABASE_URL": "@supabase-url",
    "SUPABASE_ANON_KEY": "@supabase-anon-key"
  }
}
```

## Success Metrics

### Week 2 Milestone
- [ ] Next.js project running with Shadcn/UI components
- [ ] Basic connection to existing FastAPI backend
- [ ] Jorge bot status dashboard operational

### Week 4 Milestone  
- [ ] Real-time chat interface with WebSocket connection
- [ ] Property listing integration with ML scoring
- [ ] Mobile-responsive design with PWA manifest

### Week 6 Milestone
- [ ] Full bot conversation flow testing
- [ ] Offline capability for core features
- [ ] Performance optimization (Core Web Vitals green)
- [ ] Production deployment ready

## Risk Mitigation

### Backend Integration Risks
- **Risk**: FastAPI ↔ Next.js authentication mismatch
- **Mitigation**: Use JWT tokens, test auth flow in Week 1

### Real-time Performance Risks  
- **Risk**: WebSocket latency for bot conversations
- **Mitigation**: Implement Supabase + Socket.IO fallback per research

### Mobile Performance Risks
- **Risk**: PWA offline sync complexity
- **Mitigation**: Progressive enhancement, core features work offline

This plan leverages the research recommendations while building on Jorge's existing production-ready backend infrastructure.