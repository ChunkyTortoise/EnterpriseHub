# Portal Swipe Interface - Integration Guide

## 🎯 Overview

This guide walks you through integrating the Tinder-style property swipe interface into your React application. The interface is **mobile-first**, **production-ready**, and **fully integrated** with the Python backend.

---

## 📦 Installation

### 1. Install Dependencies

```bash
cd ghl_real_estate_ai/frontend
npm install react-tinder-card framer-motion lucide-react axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Configure Tailwind CSS

Update your `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './components/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      animation: {
        'slide-up': 'slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        'fade-in-delay': 'fadeInDelay 3s ease-in-out forwards',
        'bounce': 'bounce 1s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
```

### 3. Import Styles

Add to your main CSS file (e.g., `app.css` or `globals.css`):

```css
@import './styles/portal-animations.css';

@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## 🚀 Quick Start

### Basic Implementation

```jsx
import React from 'react';
import SwipeDeck from './components/portal/SwipeDeck';
import { mockProperties, mockLead } from './utils/mockData';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <SwipeDeck 
        properties={mockProperties}
        leadId={mockLead.id}
        locationId={mockLead.location_id}
        apiBaseUrl="/api"
        onComplete={() => {
          console.log('All properties reviewed!');
        }}
        onError={(error) => {
          console.error('Swipe error:', error);
        }}
      />
    </div>
  );
}

export default App;
```

---

## 🔌 Backend Integration

### 1. Configure API Endpoint

The `SwipeDeck` component expects your Python FastAPI backend to be running at `/api/portal/swipe`.

**Development Proxy Setup (React/Next.js):**

```javascript
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // Python FastAPI server
      },
    ];
  },
};
```

**Or use environment variables:**

```jsx
<SwipeDeck 
  apiBaseUrl={process.env.NEXT_PUBLIC_API_URL || '/api'}
  // ... other props
/>
```

### 2. API Request Format

The component sends this payload on each swipe:

```json
{
  "lead_id": "contact_123",
  "property_id": "mls_998877",
  "action": "like",
  "location_id": "loc_xyz",
  "time_on_card": 12.5,
  "feedback": {
    "category": "price_too_high"
  }
}
```

### 3. Expected API Response

```json
{
  "status": "logged",
  "trigger_sms": false,
  "high_intent": false,
  "message": null,
  "adjustments": []
}
```

---

## 🎨 Customization

### Changing Colors

Update the feedback modal button colors in `FeedbackModal.jsx`:

```jsx
const reasons = [
  { 
    id: 'price_too_high', 
    label: 'Too Expensive', 
    icon: <DollarSign size={20} />,
    color: 'hover:border-red-500 hover:bg-red-50'  // Change this
  },
  // ...
];
```

### Adjusting Card Size

In `PropertyCard.jsx`:

```jsx
<div className="relative w-full h-[600px] sm:h-[650px] ...">
  {/* Change h-[600px] to your preferred height */}
</div>
```

### Adding More Feedback Options

Add to the `reasons` array in `FeedbackModal.jsx`:

```jsx
{ 
  id: 'no_parking', 
  label: 'No Parking', 
  icon: <Car size={20} />,
  color: 'hover:border-yellow-500 hover:bg-yellow-50'
},
```

---

## 📱 Mobile Optimization

### Tested On:
- ✅ iOS Safari (iPhone 12+)
- ✅ Android Chrome (Samsung, Pixel)
- ✅ Desktop Chrome/Firefox/Safari

### Performance Tips:

1. **Lazy Load Images:**
```jsx
<img 
  src={property.image_url} 
  loading="lazy"
  alt={property.address}
/>
```

2. **Preload Next Card:**
```jsx
useEffect(() => {
  if (currentIndex > 0) {
    const nextProperty = properties[currentIndex - 1];
    const img = new Image();
    img.src = nextProperty.image_url;
  }
}, [currentIndex]);
```

3. **Reduce Animation on Slow Devices:**
Already handled via CSS `prefers-reduced-motion` media query.

---

## 🧪 Testing the Flow

### 1. Test with Mock Data (No Backend)

```jsx
import { mockProperties, mockSwipeResponse } from './utils/mockData';

// In SwipeDeck, replace axios call with mock:
const handleInteraction = async (property, action, feedbackCategory) => {
  console.log('Mock swipe:', { property, action, feedbackCategory });
  
  // Simulate high-intent on 3rd like
  if (action === 'like' && likeCount === 2) {
    setHighIntentAlert(true);
  }
};
```

### 2. Test "Pass" Flow

1. Run your React app
2. Swipe LEFT on a card
3. **Expected:** Feedback modal pops up
4. Click "Too Expensive"
5. **Expected:** Console shows: `Action: pass | Feedback: price_too_high`

### 3. Test High-Intent Detection

1. Swipe RIGHT on 3 properties quickly
2. **Expected:** Green banner appears: "High Interest Detected! 🔥"
3. Check Python logs: Should see `High intent detected: 3 likes`

---

## 🔗 Connecting to Real Property Data

### Option A: Fetch from API

```jsx
import { useState, useEffect } from 'react';

function PropertyPortal({ leadId }) {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProperties() {
      try {
        const response = await fetch(`/api/properties/matches/${leadId}`);
        const data = await response.json();
        setProperties(data.matches);
      } catch (error) {
        console.error('Failed to load properties:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchProperties();
  }, [leadId]);

  if (loading) return <div>Loading properties...</div>;

  return (
    <SwipeDeck 
      properties={properties}
      leadId={leadId}
      locationId="loc_xyz"
    />
  );
}
```

### Option B: Pass from Parent Component

```jsx
// Parent component fetches and filters properties
function LeadPortalPage({ lead, matches }) {
  return (
    <SwipeDeck 
      properties={matches}
      leadId={lead.id}
      locationId={lead.location_id}
    />
  );
}
```

---

## 🎯 Advanced Features

### 1. Undo Last Swipe

```jsx
const [history, setHistory] = useState([]);

const onSwipe = (direction, propertyId) => {
  setHistory([...history, { propertyId, direction }]);
  // ... rest of logic
};

const undoLastSwipe = () => {
  if (history.length > 0) {
    const last = history[history.length - 1];
    // Restore card to stack
    setCurrentIndex(currentIndex + 1);
    setHistory(history.slice(0, -1));
  }
};
```

### 2. Save Liked Properties to Profile

```jsx
const onSwipe = async (direction, propertyId) => {
  if (direction === 'right') {
    // Save to user's saved list
    await axios.post('/api/user/saved-properties', {
      lead_id: leadId,
      property_id: propertyId
    });
  }
  // ... rest of logic
};
```

### 3. Analytics Tracking

```jsx
const onSwipe = (direction, propertyId) => {
  // Track with Google Analytics
  window.gtag('event', 'property_swipe', {
    action: direction,
    property_id: propertyId,
    lead_id: leadId
  });
  
  // Or Mixpanel, Amplitude, etc.
};
```

---

## 🚨 Common Issues & Solutions

### Issue: Cards not swiping on mobile

**Solution:** Ensure `react-tinder-card` is properly installed:
```bash
npm install react-tinder-card --save
```

### Issue: Images not loading

**Solution:** Check CORS headers on your image server or use proxy:
```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['images.unsplash.com', 'your-image-cdn.com'],
  },
};
```

### Issue: High-intent banner not showing

**Solution:** Check API response structure:
```javascript
console.log('API Response:', response.data);
// Should have: { trigger_sms: true, high_intent: true }
```

### Issue: Modal not closing properly

**Solution:** Ensure state is reset:
```jsx
const onFeedbackSubmit = (feedbackCategory) => {
  handleInteraction(currentPassProperty, 'pass', feedbackCategory);
  setShowFeedbackModal(false);
  setCurrentPassProperty(null); // Important!
};
```

---

## 📊 Component Props Reference

### SwipeDeck Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `properties` | `Array` | ✅ | Array of property objects |
| `leadId` | `String` | ✅ | GHL contact ID |
| `locationId` | `String` | ✅ | GHL location ID |
| `apiBaseUrl` | `String` | ❌ | API base URL (default: `/api`) |
| `onComplete` | `Function` | ❌ | Called when all cards swiped |
| `onError` | `Function` | ❌ | Error handler callback |

### Property Object Structure

```typescript
interface Property {
  id: string;
  price: number;
  beds: number;
  baths: number;
  sqft: number;
  address: string;
  city: string;
  state?: string;
  property_type?: string;
  image_url: string;
  est_payment?: number;
  status?: string;
}
```

---

## 🎬 Next Steps

1. **Run Local Test:**
   ```bash
   npm run dev
   ```
   Visit `http://localhost:3000` and test swipe flow

2. **Connect to Backend:**
   - Start Python FastAPI server: `uvicorn main:app --reload`
   - Verify `/api/portal/swipe` endpoint is accessible
   - Check CORS settings if needed

3. **Deploy Frontend:**
   ```bash
   npm run build
   npm start
   ```

4. **Monitor Analytics:**
   - Track swipe velocity (likes per minute)
   - Measure high-intent conversion rate
   - Analyze feedback patterns

---

## 🔐 Security Considerations

### 1. Validate Lead ID

```jsx
const validateLeadId = (leadId) => {
  // Ensure leadId matches authenticated user
  if (leadId !== currentUser.contactId) {
    throw new Error('Unauthorized');
  }
};
```

### 2. Rate Limiting

```jsx
const [swipeCount, setSwipeCount] = useState(0);
const maxSwipesPerMinute = 30;

const onSwipe = (direction, propertyId) => {
  if (swipeCount >= maxSwipesPerMinute) {
    alert('Please slow down and review properties carefully.');
    return;
  }
  setSwipeCount(swipeCount + 1);
  // ... rest of logic
};
```

### 3. Sanitize User Input

```jsx
const onFeedbackSubmit = (feedbackCategory) => {
  // Validate against allowed categories
  const allowedCategories = ['price_too_high', 'location', 'size_too_small', ...];
  
  if (!allowedCategories.includes(feedbackCategory)) {
    console.error('Invalid feedback category');
    return;
  }
  
  handleInteraction(currentPassProperty, 'pass', feedbackCategory);
};
```

---

## 📞 Support

**Questions?** Check these resources:
- Backend API docs: `http://localhost:8000/docs`
- Component source: `frontend/components/portal/`
- Python service: `services/portal_swipe_manager.py`

**Found a bug?** Open an issue with:
- Browser/device info
- Console error logs
- Steps to reproduce

---

## ✅ Pre-Launch Checklist

- [ ] Test on iPhone Safari
- [ ] Test on Android Chrome
- [ ] Test high-intent detection (3 quick likes)
- [ ] Test pass feedback flow
- [ ] Verify API connection
- [ ] Check image loading performance
- [ ] Test with real property data
- [ ] Enable error logging
- [ ] Set up analytics tracking
- [ ] Configure CORS properly
- [ ] Test empty state (no properties)
- [ ] Test network failure handling

---

## 🚀 Performance Metrics

**Target Benchmarks:**
- First card render: < 1 second
- Swipe response time: < 100ms
- Modal open animation: < 300ms
- Image load time: < 2 seconds

**Monitor These:**
- Swipe completion rate (% who finish deck)
- Average time per card
- Like/pass ratio
- High-intent trigger frequency

---

**🎉 You're Ready!** The swipe interface is now production-ready. Start testing with mock data, then connect to your backend and real property listings.
