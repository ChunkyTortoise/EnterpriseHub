# Tremor: Card Component

## Description
The Card component is a versatile container for displaying content with a clear visual boundary. It's a fundamental building block for dashboards and UI layouts.

## Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `decoration` | `"top" \| "left" \| "right" \| "bottom"` | `undefined` | The side of the card to display a colored line (border). |
| `decorationColor`| `Color` (string) | `"blue"` | The color of the decoration line. Supports all Tremor colors. |

## Example Usage

```tsx
import { Card, Metric, Text } from "@tremor/react";

export const KpiCard = () => (
  <Card decoration="top" decorationColor="blue">
    <Text>Sales</Text>
    <Metric>$ 34,743</Metric>
  </Card>
);
```

## Keywords
Card, Container, Panel, Dashboard Block, KPI, Metric, UI, Shadcn, Tremor
