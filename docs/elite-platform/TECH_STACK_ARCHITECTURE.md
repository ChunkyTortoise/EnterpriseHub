# TECH_STACK_ARCHITECTURE.md
**Quick Reference & Decision Trees**

## 🏗️ Technical Architecture Overview

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | Next.js 15 + React 19 | Best-in-class SSR, streaming, App Router |
| **Styling** | Tailwind CSS 4 + Design Tokens | Utility-first, dark mode native |
| **Components** | shadcn/ui + Aceternity UI | Copy-paste base + advanced effects |
| **Animations** | Framer Motion | Orchestration, scroll triggers, layout |
| **Maps** | Deck.gl + Mapbox GL JS | WebGL scale (1M+ points @ 60fps) |
| **Charts** | Recharts | Accessible, React-native |
| **3D** | React Three Fiber | Declarative Three.js for premium UX |
| **BI** | Lightdash Embedded | Real-time, dbt-native, embedded SDK |
| **State** | Zustand | Simpler than Redux, perfect scale |
| **ML** | SHAP + WASM | Explainability + browser inference |
| **Deployment** | Vercel | Next.js-native, auto-scaling |

## 🛠️ Key Decision Trees

### 1. Visualization Strategy
- **Static/Simple Data?** -> Recharts (SVG)
- **Geospatial < 1000 points?** -> Mapbox GL JS (Standard)
- **Geospatial > 1000 points?** -> Deck.gl (WebGL)
- **Complex 3D Property Model?** -> React Three Fiber

### 2. State Management
- **Server State?** -> TanStack Query (React Query)
- **Global UI State?** -> Zustand
- **Form State?** -> React Hook Form + Zod

### 3. Animation Strategy (4 Levels of Polish)
- **Level 1 (Essential):** Subtle hover effects (Tailwind transitions).
- **Level 2 (Standard):** Layout transitions (Framer Motion `layoutId`).
- **Level 3 (Premium):** Scroll-triggered reveals and staggered lists.
- **Level 4 (Elite):** Background beams, glowing paths, and 3D interactions.

## 🌑 Dark Mode Implementation
- **Base Color:** `#0f0f0f` (Off-black)
- **Surface Color:** `#1a1a1a`
- **Accent Color:** `#3b82f6` (Blue) or `#8b5cf6` (Purple)
- **Text:** `#f5f5f5` (Primary), `#a3a3a3` (Secondary)

## ⌨️ Keyboard Shortcut Registry
- `Cmd+K`: Global Command Palette
- `Cmd+J`: Jorge AI Chat
- `G then L`: Go to Leads
- `G then S`: Go to Sellers
- `G then D`: Go to Dashboard
