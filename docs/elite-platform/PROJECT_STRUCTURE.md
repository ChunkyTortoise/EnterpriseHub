# PROJECT_STRUCTURE.md
**Full Directory Layout & Examples**

## 📂 Elite Platform Directory Tree

```text
jorge-realestate-platform/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Authentication routes
│   │   ├── (dashboard)/        # Main dashboard layout
│   │   │   ├── dashboard/      # Executive view
│   │   │   ├── leads/          # Lead management
│   │   │   ├── properties/     # 3D Property viewer
│   │   │   └── settings/       # Account settings
│   │   └── api/                # Route handlers
│   ├── components/
│   │   ├── ui/                 # shadcn/ui base components
│   │   ├── effects/            # Aceternity/Magic UI components
│   │   ├── viz/                # Charts, Maps, 3D
│   │   ├── cards/              # LeadCard, PropertyCard
│   │   └── layout/             # Sidebar, Navbar, CmdK
│   ├── hooks/                  # Custom React hooks
│   ├── lib/
│   │   ├── store/              # Zustand stores
│   │   ├── api/                # API clients
│   │   └── utils.ts            # Utility functions
│   └── types/                  # TypeScript interfaces
├── public/                     # Static assets
├── docs/                       # Project documentation
├── tailwind.config.ts          # Tailwind 4 configuration
└── next.config.ts              # Next.js configuration
```

## 📝 Key File Examples

### `src/types/lead.ts`
```typescript
export interface Lead {
  id: string;
  name: string;
  status: 'new' | 'hot' | 'qualified' | 'dead';
  score: number;
  potentialCommission: number;
  lastInteraction: string;
  behavioralSignals: string[];
}
```

### `src/lib/store/leads.ts` (Zustand)
```typescript
import { create } from 'zustand';
import { Lead } from '@/types/lead';

interface LeadStore {
  leads: Lead[];
  activeLeadId: string | null;
  setLeads: (leads: Lead[]) => void;
  setActiveLead: (id: string) => void;
}

export const useLeadStore = create<LeadStore>((set) => ({
  leads: [],
  activeLeadId: null,
  setLeads: (leads) => set({ leads }),
  setActiveLead: (id) => set({ activeLeadId: id }),
}));
```

### `src/components/cards/LeadCard.tsx` (Framer Motion)
```tsx
import { motion } from 'framer-motion';

export const LeadCard = ({ lead }: { lead: Lead }) => {
  return (
    <motion.div
      layoutId={lead.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="p-4 bg-neutral-900 border border-neutral-800 rounded-xl"
    >
      {/* Content */}
    </motion.div>
  );
};
```
