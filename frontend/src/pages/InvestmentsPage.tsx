import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  Box,
  Button,
  Chip,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';

import { PageHeader } from '@/components/PageHeader';
import { FormDialog } from '@/components/FormDialog';
import { RHFTextField } from '@/components/form/RHFTextField';
import { RHFSelect } from '@/components/form/RHFSelect';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { investmentHooks, usePortfolioSummary } from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { investmentTypes } from '@/constants/enums';
import { formatINR, formatPercent, humanize } from '@/utils/format';
import type { Investment, InvestmentInput } from '@/types/finance';

interface FormValues {
  name: string;
  investment_type: string;
  platform: string;
  invested_amount: string;
  current_value: string;
  purchase_date: string;
}

const empty = (): FormValues => ({
  name: '', investment_type: 'mutual_funds', platform: '',
  invested_amount: '', current_value: '', purchase_date: '',
});

export function InvestmentsPage() {
  const toast = useToast();
  const { data, isLoading } = investmentHooks.useList();
  const summary = usePortfolioSummary();
  const createM = investmentHooks.useCreate();
  const updateM = investmentHooks.useUpdate();
  const removeM = investmentHooks.useRemove();

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Investment | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Investment | null>(null);

  const { control, handleSubmit, reset } = useForm<FormValues>({ defaultValues: empty() });

  useEffect(() => {
    if (!open) return;
    reset(
      editing
        ? {
            name: editing.name, investment_type: editing.investment_type, platform: editing.platform ?? '',
            invested_amount: editing.invested_amount, current_value: editing.current_value,
            purchase_date: editing.purchase_date ?? '',
          }
        : empty(),
    );
  }, [open, editing, reset]);

  const onSubmit = handleSubmit(async (v) => {
    const body: InvestmentInput = {
      name: v.name, investment_type: v.investment_type, platform: v.platform || null,
      invested_amount: Number(v.invested_amount), current_value: Number(v.current_value || v.invested_amount),
      purchase_date: v.purchase_date || null,
    };
    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Investment updated' : 'Investment added');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  });

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await removeM.mutateAsync(deleteTarget.id);
      toast.success('Investment deleted');
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <PageHeader
        title="Investments"
        subtitle="Your portfolio and returns"
        action={
          <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={() => { setEditing(null); setOpen(true); }}>
            Add
          </Button>
        }
      />

      {summary.data && (
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, mb: 3 }}>
          <KpiCard title="Invested" value={formatINR(summary.data.total_invested)} accent="info.main" />
          <KpiCard title="Current Value" value={formatINR(summary.data.total_current_value)} accent="primary.main" />
          <KpiCard
            title="Total Returns"
            value={formatINR(summary.data.total_returns)}
            accent={Number(summary.data.total_returns) >= 0 ? 'success.main' : 'error.main'}
            caption={formatPercent(summary.data.total_returns_percent)}
          />
        </Box>
      )}

      {isLoading && <LoadingSkeleton cards={0} rows={5} />}
      {!isLoading && data && data.length === 0 && (
        <EmptyState title="No investments yet" description="Add a holding to track its value and returns." actionLabel="Add investment" onAction={() => { setEditing(null); setOpen(true); }} />
      )}

      {!isLoading && data && data.length > 0 && (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell align="right">Invested</TableCell>
                <TableCell align="right">Current</TableCell>
                <TableCell align="right">Returns</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((inv) => {
                const positive = Number(inv.returns_value) >= 0;
                return (
                  <TableRow key={inv.id} hover>
                    <TableCell>{inv.name}</TableCell>
                    <TableCell><Chip label={humanize(inv.investment_type)} size="small" variant="outlined" /></TableCell>
                    <TableCell align="right">{formatINR(inv.invested_amount)}</TableCell>
                    <TableCell align="right">{formatINR(inv.current_value)}</TableCell>
                    <TableCell align="right" sx={{ color: positive ? 'success.main' : 'error.main' }}>
                      {formatINR(inv.returns_value)} ({formatPercent(inv.returns_percent)})
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => { setEditing(inv); setOpen(true); }}><EditRoundedIcon fontSize="small" /></IconButton>
                      <IconButton size="small" onClick={() => setDeleteTarget(inv)}><DeleteRoundedIcon fontSize="small" /></IconButton>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <FormDialog
        open={open}
        title={editing ? 'Edit investment' : 'Add investment'}
        onClose={() => setOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <RHFTextField control={control} name="name" label="Name" required />
          <RHFSelect control={control} name="investment_type" label="Type" options={investmentTypes} />
          <RHFTextField control={control} name="platform" label="Platform / broker" />
          <RHFTextField control={control} name="invested_amount" label="Invested amount (₹)" type="number" required />
          <RHFTextField control={control} name="current_value" label="Current value (₹)" type="number" />
          <RHFTextField control={control} name="purchase_date" label="Purchase date" type="date" />
        </Stack>
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete investment?"
        message={`Delete "${deleteTarget?.name ?? ''}"?`}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={removeM.isPending}
      />
    </Box>
  );
}
