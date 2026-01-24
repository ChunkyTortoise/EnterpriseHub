# Shadcn/UI: Button Component

A versatile button component that follows the Shadcn/UI design system.

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `string` | `"default"` | The visual style: `"default"`, `"destructive"`, `"outline"`, `"secondary"`, `"ghost"`, `"link"`. |
| `size` | `string` | `"default"` | The size of the button: `"default"`, `"sm"`, `"lg"`, `"icon"`. |
| `asChild` | `boolean` | `false` | Whether to render the button as its child component (useful for Radix UI integration). |

## Usage

```tsx
import { Button } from "@/components/ui/button"

export default function ButtonDemo() {
  return (
    <div className="flex gap-4">
      <Button variant="default">Default</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="ghost" size="icon">
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}
```

## Design Tokens
- Border Radius: `var(--radius)`
- Font: Inter/Geist
- Colors: Primary, Secondary, Accent, Destructive, Ghost

## Tags
Button, UI, Shadcn, Input, Interaction, Form, CTA
