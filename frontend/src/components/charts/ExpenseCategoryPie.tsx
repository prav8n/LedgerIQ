import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { Box, Typography } from '@mui/material';
import { useChartColors } from '@/components/charts/useChartColors';
import { formatINR, humanize, toNumber } from '@/utils/format';
import type { CategoryAmount } from '@/types/dashboard';

interface Props {
  items: CategoryAmount[];
}

export function ExpenseCategoryPie({ items }: Props) {
  const colors = useChartColors();
  const data = items.map((i) => ({ name: humanize(i.category), value: toNumber(i.amount) }));

  if (data.length === 0) {
    return (
      <Box sx={{ height: '100%', display: 'grid', placeItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No expenses this month
        </Typography>
      </Box>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius="55%"
          outerRadius="80%"
          paddingAngle={2}
          stroke="none"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={colors.categorical[i % colors.categorical.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value) => formatINR(value as number)}
          contentStyle={{
            background: colors.tooltipBg,
            border: `1px solid ${colors.tooltipBorder}`,
            borderRadius: 8,
          }}
        />
        <Legend iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  );
}
