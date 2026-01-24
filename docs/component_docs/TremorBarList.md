# Tremor: BarList Component

The BarList component is used to display a list of bars, ideal for showing rankings or relative distributions.

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `any[]` | `[]` | Array of data objects containing `name` and `value`. |
| `valueFormatter` | `(value: number) => string` | `(value) => value.toString()` | Function to format the values. |
| `color` | `Color` | `"blue"` | The color of the bars. |
| `showAnimation` | `boolean` | `false` | Whether to show an entrance animation. |

## Usage

```tsx
import { BarList, Card, Title, Bold, Flex, Text } from "@tremor/react";

const data = [
  { name: "/home", value: 456 },
  { name: "/imprint", value: 351 },
  { name: "/cancellation", value: 271 },
];

export default function BarListHero() {
  return (
    <Card className="max-w-md">
      <Title>Website Analytics</Title>
      <Flex className="mt-4">
        <Text><Bold>Source</Bold></Text>
        <Text><Bold>Visits</Bold></Text>
      </Flex>
      <BarList data={data} className="mt-2" />
    </Card>
  );
}
```

## Tags
BarList, List, Ranking, Analytics, Tremor, Visualization
