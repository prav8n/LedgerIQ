import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  Box,
  Button,
  Card,
  CardContent,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
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
import { budgetHooks } from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { budgetPeriods, expenseCategories } from '@/constants/enums';
import { formatINR, formatPercent, humanize } from '@/utils/format';
import type { Budget, BudgetInput } from '@/types/finance';

interface FormValues {
  category: string;
  amount: string;
  period: string;
  start_date: string;
}

const firstOfMonth = () => {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
};

const statusColor = (s: Budget['status']): 'success' | 'warning' | 'error' =>
  s === 'red' ? 'error' : s === 'yellow' ? 'warning' : 'success';

export function BudgetsPage() {
  const toast = useToast();
  const { data, isLoading } = budgetHooks.useList();
  const createM = budgetHooks.useCreate();
  const updateM = budgetHooks.useUpdate();
  const removeM = budgetHooks.useRemove();

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Budget | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Budget | null>(null);

  const { control, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: { category: 'food', amount: '', period: 'monthly', start_date: firstOfMonth() },
  });

  useEffect(() => {
    if (!open) return;
    reset(
      editing
        ? { category: editing.category, amount: editing.amount, period: editing.period, start_date: editing.start_date }
        : { category: 'food', amount: '', period: 'monthly', start_date: firstOfMonth() },
    );
  }, [open, editing, reset]);

  const onSubmit = handleSubmit(async (v) => {
    const body: BudgetInput = {
      category: v.category,
      amount: Number(v.amount),
      period: v.period,
      start_date: v.start_date,
    };
    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Budget updated' : 'Budget created');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  });

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await removeM.mutateAsync(deleteTarget.id);
      toast.success('Budget deleted');
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <PageHeader
        title="Budgets"
        subtitle="Per-category spending limits"
        action={
          <Button
            variant="contained"
            startIcon={<AddRoundedIcon />}
            onClick={() => {
              setEditing(null);
              setOpen(true);
            }}
          >
            Add budget
          </Button>
        }
      />

      {isLoading && <LoadingSkeleton cards={3} rows={0} />}
      {!isLoading && data && data.length === 0 && (
        <EmptyState
          title="No budgets yet"
          description="Create a budget to track spending against a category."
          actionLabel="Add budget"
          onAction={() => {
            setEditing(null);
            setOpen(true);
          }}
        />
      )}

      {!isLoading && data && data.length > 0 && (
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' } }}>
          {data.map((b) => (
            <Card key={b.id}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
                  <Box>
                    <Typography variant="h6">{humanize(b.category)}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {humanize(b.period)}
                    </Typography>
                  </Box>
                  <Box>
                    <IconButton size="small" onClick={() => { setEditing(b); setOpen(true); }}>
                      <EditRoundedIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => setDeleteTarget(b)}>
                      <DeleteRoundedIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Stack>
                <Typography variant="h5" fontWeight={800}>
                  {formatINR(b.spent)} <Typography component="span" variant="body2" color="text.secondary">/ {formatINR(b.amount)}</Typography>
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(b.percent_used, 100)}
                  color={statusColor(b.status)}
                  sx={{ height: 8, borderRadius: 4, my: 1 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {formatPercent(b.percent_used)} used · {formatINR(b.remaining)} left
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      <FormDialog
        open={open}
        title={editing ? 'Edit budget' : 'Add budget'}
        onClose={() => setOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <RHFSelect control={control} name="category" label="Category" options={expenseCategories} />
          <RHFTextField control={control} name="amount" label="Amount (₹)" type="number" required />
          <RHFSelect control={control} name="period" label="Period" options={budgetPeriods} />
          <RHFTextField control={control} name="start_date" label="Start date" type="date" required />
        </Stack>
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete budget?"
        message="This budget will be removed."
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={removeM.isPending}
      />
    </Box>
  );
}
