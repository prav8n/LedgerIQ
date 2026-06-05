import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useChartColors } from '@/components/charts/useChartColors';
import { formatINR, formatINRCompact } from '@/utils/format';

export interface TrendSeries {
  key: string;
  name: string;
  color: string;
}

export type TrendDatum = Record<string, string | number>;

interface Props {
  data: TrendDatum[];
  series: TrendSeries[];
  variant?: 'line' | 'area';
  showLegend?: boolean;
}

/** Multi-series line/area trend chart over a `label` x-axis. */
export function TrendChart({ data, series, variant = 'line', showLegend = true }: Props) {
  const colors = useChartColors();

  const axisProps = {
    tick: { fill: colors.axis, fontSize: 12 },
    tickLine: false,
  } as const;
  const tooltip = (
    <Tooltip
      formatter={(value) => formatINR(value as number)}
      contentStyle={{
        background: colors.tooltipBg,
        border: `1px solid ${colors.tooltipBorder}`,
        borderRadius: 8,
      }}
    />
  );
  const grid = <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} vertical={false} />;
  const xAxis = <XAxis dataKey="label" {...axisProps} />;
  const yAxis = (
    <YAxis
      tickFormatter={(v) => formatINRCompact(v as number)}
      {...axisProps}
      axisLine={false}
      width={60}
    />
  );

  if (variant === 'area') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <defs>
            {series.map((s) => (
              <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={s.color} stopOpacity={0.35} />
                <stop offset="95%" stopColor={s.color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          {grid}
          {xAxis}
          {yAxis}
          {tooltip}
          {showLegend && <Legend iconType="circle" />}
          {series.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              fill={`url(#grad-${s.key})`}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        {grid}
        {xAxis}
        {yAxis}
        {tooltip}
        {showLegend && <Legend iconType="circle" />}
        {series.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name}
            stroke={s.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
