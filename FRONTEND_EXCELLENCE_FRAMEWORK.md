# Gemini CLI Frontend Excellence Framework (2026 Edition)

This framework is designed to elevate Gemini CLI from a general-purpose assistant to an elite frontend development tool. It integrates state-of-the-art patterns for React 19, Tailwind CSS 4, and modern design systems.

---

## 1. Prompt Template Library

Optimized prompts for consistent, high-quality frontend output.

### 1.1 Atomic Component Generation
```markdown
Generate a [Component Name] using React 19 and Tailwind 4.
- Follow Atomic Design principles (Atom/Molecule/Organism).
- Use TypeScript with strict typing (interfaces for props).
- Implement responsive design with mobile-first approach.
- Include accessibility (ARIA labels, keyboard navigation).
- Use `framer-motion` for subtle entrance/interaction animations.
- Stack: React 19 (functional components), Tailwind 4 utility classes, Lucide icons.
```

### 1.2 Design System Token Integration
```markdown
Define a semantic color palette and spacing system for [Theme Name].
- Provide a set of CSS variables for: primitives (blue-500), semantics (action-primary), and components (button-bg).
- Ensure WCAG 2.2 AA contrast compliance.
- Include dark/light mode variants using Tailwind's `dark:` modifier.
```

### 1.3 Complex Data Visualization
```markdown
Create a responsive dashboard widget for [Data Type] using shadcn/charts or Tremor patterns.
- Implement real-time update simulations.
- Ensure the chart is accessible (screen reader descriptions).
- Use a fluid layout that adapts to container queries.
```

---

## 2. System Instructions

Integrate these into your Gemini CLI configuration (e.g., `.geminiignore` or custom system prompt).

### Architectural Mandates
- **React 19 Patterns:** Use `use` hook for data fetching and `Action` patterns for forms.
- **Tailwind 4 First:** Leverage native CSS variables and `@theme` blocks. No legacy CSS-in-JS.
- **Composition over Inheritance:** Use `Children` and `Slot` patterns (Radix UI style) for flexibility.
- **Strict Typing:** No `any`. Use generics for reusable components.

### UI/UX Standards
- **Aesthetic:** "Glassmorphism" for overlays, "Skeuomorphic depth" for primary buttons, and ultra-refined micro-interactions.
- **Motion:** All state transitions should have a `duration-200` ease-in-out minimum.
- **Accessibility:** 100% Lighthouse Accessibility score is the baseline.

---

## 3. Configuration Files (Optimized)

### ESLint 9+ (`eslint.config.mjs`)
Includes `jsx-a11y` and stricter TS rules.

```javascript
import jsxA11y from 'eslint-plugin-jsx-a11y';
// ... existing imports
export default tseslint.config(
  // ... existing configs
  jsxA11y.flatConfigs.recommended,
  {
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      'react/no-array-index-key': 'error',
      'jsx-a11y/anchor-is-valid': 'warn',
    }
  }
);
```

---

## 4. Design Token Framework

Scaleable structure for multi-brand/multi-mode support.

| Category | Token Pattern | Example |
| :--- | :--- | :--- |
| **Primitive** | `--color-[name]-[scale]` | `--color-blue-500: #3b82f6;` |
| **Semantic** | `--[usage]-[state]` | `--bg-action-hover: var(--color-blue-600);` |
| **Component** | `--[comp]-[part]-[attr]` | `--btn-primary-bg: var(--bg-action-default);` |

---

## 5. Component Template Catalog (Samples)

### The "Elite" Button
```tsx
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = ({ className, variant = 'primary', size = 'md', ...props }: ButtonProps) => {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "rounded-xl font-medium transition-all focus:ring-2 focus:ring-primary/50",
        variant === 'primary' && "bg-primary text-primary-foreground shadow-lg hover:shadow-primary/25",
        // ... variants
        className
      )}
      {...props}
    />
  );
};
```

---

## 6. Aesthetic Guidelines

- **Typography:** Inter for UI, Playfair Display for headers (Fluid sizing: `clamp(2rem, 5vw, 4rem)`).
- **Color:** Deep oceanic blues with neon accents (Primary: `#00D2FF`, Secondary: `#0045FF`).
- **Depth:** Use `backdrop-blur-md` for all modals and dropdowns.

---

## 7. Quality Checklist

- [ ] **Accessibility:** Tab-navigable? Contrast pass? Aria-labels present?
- [ ] **Performance:** Minimal re-renders? Image optimization? Bundle size impact?
- [ ] **Responsiveness:** Works on 320px and 2560px?
- [ ] **Code Quality:** Type-safe? No console logs? Lint pass?

---

## 8. Integration Workflow

1. **Phase 1: Environment Setup** (Run `npm install eslint-plugin-jsx-a11y prettier-plugin-tailwindcss`)
2. **Phase 2: Global Styles** (Implement the Design Token Framework in `globals.css`)
3. **Phase 3: Component Scaffolding** (Use the Prompt Library to generate core UI)
4. **Phase 4: Automated Validation** (Integrate the Quality Checklist into CI/CD)
