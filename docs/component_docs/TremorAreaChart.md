# Tremor: AreaChart Component

The AreaChart component is used to display time-series data with a filled area below the line.

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `any[]` | `[]` | Array of data objects to be displayed. |
| `index` | `string` | `undefined` | The key of the data object to be used for the x-axis. |
| `categories` | `string[]` | `[]` | Array of keys of the data object to be used for the y-axis lines. |
| `colors` | `Color[]` | `[]` | Array of Tremor colors for the categories. |
| `valueFormatter` | `(value: number) => string` | `(value) => value.toString()` | Function to format the y-axis values. |
| `showLegend` | `boolean` | `true` | Whether to show the legend. |
| `yAxisWidth` | `number` | `56` | The width of the y-axis in pixels. |

## Usage

```tsx
import { AreaChart, Card, Title } from "@tremor/react";

const chartdata = [
  { date: "Jan 22", Semi: 2890, "The Sun": 2338 },
  { date: "Feb 22", Semi: 2756, "The Sun": 2103 },
  { date: "Mar 22", Semi: 3322, "The Sun": 2194 },
];

const dataFormatter = (number: number) => {
  return "$ " + Intl.NumberFormat("us").format(number).toString();
};

export default function AreaChartHero() {
  return (
    <Card>
      <Title>Newsletter Revenue over time (USD)</Title>
      <AreaChart
        className="h-72 mt-4"
        data={chartdata}
        index="date"
        categories={["Semi", "The Sun"]}
        colors={["indigo", "cyan"]}
        valueFormatter={dataFormatter}
      />
    </Card>
  );
}
```

## Tags
AreaChart, Chart, Visualization, Data, Tremor, Time Series, Revenue
