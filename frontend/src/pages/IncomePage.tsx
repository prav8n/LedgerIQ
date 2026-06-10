import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  Box,
  Button,
  Chip,
  IconButton,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import PaymentsRoundedIcon from '@mui/icons-material/PaymentsRounded';
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { PageHeader } from '@/components/PageHeader';
import { FormDialog } from '@/components/FormDialog';
import { RHFTextField } from '@/components/form/RHFTextField';
import { RHFSelect } from '@/components/form/RHFSelect';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { ChartCard } from '@/components/charts/ChartCard';
import { useChartColors } from '@/components/charts/useChartColors';
import { PeriodSelector } from '@/components/PeriodSelector';
import {
  MONTH_LABELS,
  defaultPeriod,
  fyLabel,
  fyStartYear,
  periodLabel,
  shiftPeriod,
  type PeriodState,
} from '@/utils/period';
import {
  incomeHooks,
  useCreateIncome,
  useRemoveIncome,
  useUpdateIncome,
} from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { incomeCategories, type Option } from '@/constants/enums';
import { formatINR, humanize, toNumber } from '@/utils/format';
import type { Income, IncomeInput } from '@/types/finance';

// --- Date constants (computed once) -------------------------------------
const NOW = new Date();
const CURRENT_YEAR = NOW.getFullYear();
const CURRENT_MONTH = NOW.getMonth() + 1; // 1-12

const MONTHS: Option[] = MONTH_LABELS.map((label, i) => ({ value: String(i + 1), label }));

// Breakdown buckets per spec: Salary / Bonus / Freelance / Other.
const TYPE_BUCKETS = ['salary', 'bonus', 'freelance', 'other'];
const bucketOf = (category: string): string =>
  TYPE_BUCKETS.includes(category) ? category : 'other';

const ROWS_PER_PAGE = 10;

const year4 = (iso: string): number => Number(iso.slice(0, 4));
const month2 = (iso: string): number => Number(iso.slice(5, 7));
const monthYearLabel = (iso: string): string =>
  `${MONTHS[month2(iso) - 1]?.label ?? ''} ${year4(iso)}`;

interface FormValues {
  category: string;
  source: string;
  amount: string;
  month: string;
  year: string;
  notes: string;
}

const emptyForm = (): FormValues => ({
  category: 'salary',
  source: '',
  amount: '',
  month: String(CURRENT_MONTH),
  year: String(CURRENT_YEAR),
  notes: '',
});

export function IncomePage() {
  const toast = useToast();
  const colors = useChartColors();

  const { data, isLoading } = incomeHooks.useList();
  const createM = useCreateIncome();
  const updateM = useUpdateIncome();
  const removeM = useRemoveIncome();

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Income | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Income | null>(null);

  // Summary period selector. Null = follow the most recent month with income.
  const [periodOverride, setPeriodOverride] = useState<PeriodState | null>(null);

  // Filters + pagination (client-side over the full record set).
  const [typeFilter, setTypeFilter] = useState('');
  const [monthFilter, setMonthFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [page, setPage] = useState(0);

  const { control, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: emptyForm(),
  });

  useEffect(() => {
    if (!open) return;
    reset(
      editing
        ? {
            category: editing.category,
            source: editing.source,
            amount: editing.amount,
            month: String(month2(editing.received_date)),
            year: String(year4(editing.received_date)),
            notes: editing.notes ?? '',
          }
        : emptyForm(),
    );
  }, [open, editing, reset]);

  // Reset to the first page whenever the filters change.
  useEffect(() => {
    setPage(0);
  }, [typeFilter, monthFilter, yearFilter]);

  // Default the summary to the most recent month that has income (records come
  // back sorted newest-first), so freshly added income is visible immediately.
  const latest = useMemo<PeriodState | null>(() => {
    const all = data ?? [];
    if (all.length === 0) return null;
    const top = all[0].received_date;
    return { granularity: 'monthly', month: month2(top), year: year4(top) };
  }, [data]);

  const period: PeriodState = periodOverride ?? latest ?? defaultPeriod('monthly');
  const prev = shiftPeriod(period, -1);
  const fyStart = fyStartYear(period);
  const fyFrom = `${fyStart}-04-01`;
  const fyTo = `${fyStart + 1}-03-31`;

  // ---- Summary for the selected month and its financial year (Apr–Mar) ----
  const summary = useMemo(() => {
    const all = data ?? [];
    let selected = 0;
    let previous = 0;
    let fyTotal = 0;
    const byType: Record<string, number> = { salary: 0, bonus: 0, freelance: 0, other: 0 };

    for (const r of all) {
      const amt = toNumber(r.amount);
      const isoDate = r.received_date;
      const y = year4(isoDate);
      const m = month2(isoDate);
      if (isoDate >= fyFrom && isoDate <= fyTo) {
        fyTotal += amt;
        byType[bucketOf(r.category)] += amt;
      }
      if (y === period.year && m === period.month) selected += amt;
      if (y === prev.year && m === prev.month) previous += amt;
    }

    const mom = previous > 0 ? ((selected - previous) / previous) * 100 : null;
    return { selected, previous, fyTotal, mom, byType };
  }, [data, period.year, period.month, prev.year, prev.month, fyFrom, fyTo]);

  const donutData = useMemo(
    () =>
      TYPE_BUCKETS.map((t) => ({ name: humanize(t), value: summary.byType[t] })).filter(
        (d) => d.value > 0,
      ),
    [summary],
  );

  // Year options for the filter, derived from the data plus the current year.
  const filterYears = useMemo(() => {
    const years = new Set<number>([CURRENT_YEAR]);
    (data ?? []).forEach((r) => years.add(year4(r.received_date)));
    return Array.from(years)
      .sort((a, b) => b - a)
      .map((y) => ({ value: String(y), label: String(y) }));
  }, [data]);

  // Year options for the form (recent range + the record being edited).
  const formYears = useMemo(() => {
    const years = new Set<number>();
    for (let i = 0; i < 12; i += 1) years.add(CURRENT_YEAR + 1 - i);
    if (editing) years.add(year4(editing.received_date));
    return Array.from(years)
      .sort((a, b) => b - a)
      .map((y) => ({ value: String(y), label: String(y) }));
  }, [editing]);

  const filtered = useMemo(() => {
    return (data ?? []).filter((r) => {
      if (typeFilter && r.category !== typeFilter) return false;
      if (monthFilter && month2(r.received_date) !== Number(monthFilter)) return false;
      if (yearFilter && String(year4(r.received_date)) !== yearFilter) return false;
      return true;
    });
  }, [data, typeFilter, monthFilter, yearFilter]);

  const paged = filtered.slice(page * ROWS_PER_PAGE, page * ROWS_PER_PAGE + ROWS_PER_PAGE);

  const openAdd = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (r: Income) => {
    setEditing(r);
    setOpen(true);
  };

  const onSubmit = handleSubmit(async (v) => {
    const amount = Number(v.amount);
    if (!(amount > 0)) {
      toast.error('Amount must be greater than 0');
      return;
    }
    const body: IncomeInput = {
      source: v.source.trim(),
      amount,
      category: v.category,
      received_date: `${v.year}-${v.month.padStart(2, '0')}-01`,
      notes: v.notes.trim() || null,
    };
    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Income updated' : 'Income added');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  });

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await removeM.mutateAsync(deleteTarget.id);
      toast.success('Income deleted');
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  };

  const hasData = Boolean(data && data.length > 0);

  return (
    <Box>
      <PageHeader
        title="Income"
        subtitle="Salary, bonuses, freelance and other earnings"
        action={
          <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={openAdd}>
            Add income
          </Button>
        }
      />

      {!isLoading && (
        <Box mb={3}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            alignItems={{ xs: 'stretch', sm: 'center' }}
            spacing={2}
            mb={2}
          >
            <Typography variant="h6">Summary</Typography>
            <PeriodSelector
              value={period}
              onChange={setPeriodOverride}
              granularities={['monthly']}
            />
          </Stack>
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' },
            }}
          >
            <Box
              sx={{
                display: 'grid',
                gap: 2,
                gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
              }}
            >
              <KpiCard
                title={periodLabel(period)}
                value={formatINR(summary.selected)}
                icon={<PaymentsRoundedIcon />}
                accent="success.main"
                caption="vs previous month"
                delta={summary.mom ?? undefined}
              />
              <KpiCard
                title={fyLabel(fyStart)}
                value={formatINR(summary.fyTotal)}
                accent="primary.main"
                caption="Financial year (Apr–Mar)"
              />
              <KpiCard
                title={periodLabel(prev)}
                value={formatINR(summary.previous)}
                accent="info.main"
                caption="Previous month"
              />
            </Box>

            <ChartCard title={`By type · ${fyLabel(fyStart)}`} height={200}>
            {donutData.length === 0 ? (
              <Box sx={{ height: '100%', display: 'grid', placeItems: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  No income this financial year
                </Typography>
              </Box>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={donutData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="55%"
                    outerRadius="80%"
                    paddingAngle={2}
                    stroke="none"
                  >
                    {donutData.map((_, i) => (
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
                    itemStyle={{ color: colors.text }}
                    labelStyle={{ color: colors.text }}
                  />
                  <Legend iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            )}
            </ChartCard>
          </Box>
        </Box>
      )}

      {isLoading && <LoadingSkeleton cards={0} rows={6} />}

      {!isLoading && !hasData && (
        <EmptyState
          icon={<PaymentsRoundedIcon />}
          title="No income yet"
          description="Add your salary, bonuses, freelance and other earnings to track cash inflow."
          actionLabel="Add income"
          onAction={openAdd}
        />
      )}

      {!isLoading && hasData && (
        <>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} mb={2}>
            <TextField
              select
              size="small"
              label="Type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              sx={{ minWidth: 160 }}
            >
              <MenuItem value="">All types</MenuItem>
              {incomeCategories.map((o) => (
                <MenuItem key={o.value} value={o.value}>
                  {o.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label="Month"
              value={monthFilter}
              onChange={(e) => setMonthFilter(e.target.value)}
              sx={{ minWidth: 140 }}
            >
              <MenuItem value="">All months</MenuItem>
              {MONTHS.map((o) => (
                <MenuItem key={o.value} value={o.value}>
                  {o.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label="Year"
              value={yearFilter}
              onChange={(e) => setYearFilter(e.target.value)}
              sx={{ minWidth: 120 }}
            >
              <MenuItem value="">All years</MenuItem>
              {filterYears.map((o) => (
                <MenuItem key={o.value} value={o.value}>
                  {o.label}
                </MenuItem>
              ))}
            </TextField>
          </Stack>

          {filtered.length === 0 ? (
            <EmptyState
              icon={<PaymentsRoundedIcon />}
              title="No matching income"
              description="No records match the selected filters. Try clearing them."
            />
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Notes</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paged.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>{monthYearLabel(r.received_date)}</TableCell>
                      <TableCell>
                        <Chip label={humanize(r.category)} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{r.source}</TableCell>
                      <TableCell
                        sx={{
                          color: 'text.secondary',
                          maxWidth: 240,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {r.notes ?? '—'}
                      </TableCell>
                      <TableCell align="right">{formatINR(r.amount)}</TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={() => openEdit(r)}>
                          <EditRoundedIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" onClick={() => setDeleteTarget(r)}>
                          <DeleteRoundedIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {filtered.length > ROWS_PER_PAGE && (
                <TablePagination
                  component="div"
                  count={filtered.length}
                  page={page}
                  onPageChange={(_, p) => setPage(p)}
                  rowsPerPage={ROWS_PER_PAGE}
                  rowsPerPageOptions={[ROWS_PER_PAGE]}
                />
              )}
            </TableContainer>
          )}
        </>
      )}

      <FormDialog
        open={open}
        title={editing ? 'Edit income' : 'Add income'}
        onClose={() => setOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <RHFSelect control={control} name="category" label="Type" options={incomeCategories} />
          <RHFTextField
            control={control}
            name="source"
            label="Source / description"
            required
            autoFocus
          />
          <RHFTextField control={control} name="amount" label="Amount (₹)" type="number" required />
          <Stack direction="row" spacing={2}>
            <RHFSelect control={control} name="month" label="Month" options={MONTHS} />
            <RHFSelect control={control} name="year" label="Year" options={formYears} />
          </Stack>
          <RHFTextField control={control} name="notes" label="Notes" multiline />
        </Stack>
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete income?"
        message={`Delete "${deleteTarget?.source ?? ''}"${
          deleteTarget ? ` (${formatINR(deleteTarget.amount)})` : ''
        }? This cannot be undone.`}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={removeM.isPending}
      />
    </Box>
  );
}
