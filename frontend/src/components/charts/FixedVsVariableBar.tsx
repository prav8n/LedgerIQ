import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useChartColors } from '@/components/charts/useChartColors';
import { formatINR, formatINRCompact, toNumber } from '@/utils/format';
import type { FixedVariable } from '@/types/dashboard';

interface Props {
  data: FixedVariable;
}

export function FixedVsVariableBar({ data }: Props) {
  const colors = useChartColors();
  const chartData = [
    { name: 'Fixed', amount: toNumber(data.fixed) },
    { name: 'Variable', amount: toNumber(data.variable) },
  ];
  const barColors = [colors.info, colors.warning];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} vertical={false} />
        <XAxis dataKey="name" tick={{ fill: colors.axis, fontSize: 12 }} tickLine={false} />
        <YAxis
          tickFormatter={(v) => formatINRCompact(v as number)}
          tick={{ fill: colors.axis, fontSize: 12 }}
          tickLine={false}
          axisLine={false}
          width={60}
        />
        <Tooltip
          cursor={{ fill: colors.grid, opacity: 0.3 }}
          formatter={(value) => formatINR(value as number)}
          contentStyle={{
            background: colors.tooltipBg,
            border: `1px solid ${colors.tooltipBorder}`,
            borderRadius: 8,
          }}
        />
        <Bar dataKey="amount" radius={[8, 8, 0, 0]} maxBarSize={90}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={barColors[i % barColors.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
