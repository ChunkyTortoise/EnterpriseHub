# Shadcn/UI: Input Component

A standard text input component for forms and data entry.

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `string` | `"text"` | The HTML input type (text, email, password, etc.). |
| `placeholder` | `string` | `""` | Placeholder text. |
| `disabled` | `boolean` | `false` | Whether the input is disabled. |

## Usage

```tsx
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function InputWithLabel() {
  return (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input type="email" id="email" placeholder="Email" />
    </div>
  )
}
```

## Design Tokens
- Border: `1px solid var(--input)`
- Ring: `var(--ring)`
- Background: `var(--background)`

## Tags
Input, Form, Text, Field, Shadcn, UI
