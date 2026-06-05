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
import { subscriptionHooks, useSubscriptionSummary } from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { frequencies, paymentMethods, subscriptionCategories } from '@/constants/enums';
import { formatDate, formatINR, humanize } from '@/utils/format';
import type { Subscription, SubscriptionInput } from '@/types/finance';

interface FormValues {
  name: string;
  category: string;
  amount: string;
  billing_cycle: string;
  start_date: string;
  next_billing_date: string;
  payment_method: string;
  reminder_days: string;
}

const today = () => new Date().toISOString().slice(0, 10);
const empty = (): FormValues => ({
  name: '', category: 'streaming', amount: '', billing_cycle: 'monthly',
  start_date: today(), next_billing_date: today(), payment_method: 'auto_debit', reminder_days: '3',
});

export function SubscriptionsPage() {
  const toast = useToast();
  const { data, isLoading } = subscriptionHooks.useList();
  const summary = useSubscriptionSummary();
  const createM = subscriptionHooks.useCreate();
  const updateM = subscriptionHooks.useUpdate();
  const removeM = subscriptionHooks.useRemove();

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Subscription | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Subscription | null>(null);

  const { control, handleSubmit, reset } = useForm<FormValues>({ defaultValues: empty() });

  useEffect(() => {
    if (!open) return;
    reset(
      editing
        ? {
            name: editing.name, category: editing.category, amount: editing.amount,
            billing_cycle: editing.billing_cycle, start_date: editing.start_date,
            next_billing_date: editing.next_billing_date, payment_method: editing.payment_method,
            reminder_days: String(editing.reminder_days),
          }
        : empty(),
    );
  }, [open, editing, reset]);

  const onSubmit = handleSubmit(async (v) => {
    const body: SubscriptionInput = {
      name: v.name, category: v.category, amount: Number(v.amount), billing_cycle: v.billing_cycle,
      start_date: v.start_date, next_billing_date: v.next_billing_date,
      payment_method: v.payment_method, reminder_days: Number(v.reminder_days),
    };
    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Subscription updated' : 'Subscription added');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  });

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await removeM.mutateAsync(deleteTarget.id);
      toast.success('Subscription deleted');
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <PageHeader
        title="Subscriptions"
        subtitle="Recurring costs and renewals"
        action={
          <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={() => { setEditing(null); setOpen(true); }}>
            Add
          </Button>
        }
      />

      {summary.data && (
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, mb: 3 }}>
          <KpiCard title="Active" value={String(summary.data.active_count)} accent="info.main" />
          <KpiCard title="Monthly Cost" value={formatINR(summary.data.total_monthly_cost)} accent="primary.main" />
          <KpiCard title="Yearly Cost" value={formatINR(summary.data.total_yearly_cost)} accent="secondary.main" />
        </Box>
      )}

      {isLoading && <LoadingSkeleton cards={0} rows={5} />}
      {!isLoading && data && data.length === 0 && (
        <EmptyState title="No subscriptions yet" description="Track recurring services and their renewal dates." actionLabel="Add subscription" onAction={() => { setEditing(null); setOpen(true); }} />
      )}

      {!isLoading && data && data.length > 0 && (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Category</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell>Cycle</TableCell>
                <TableCell>Next renewal</TableCell>
                <TableCell align="right">Per month</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((s) => (
                <TableRow key={s.id} hover>
                  <TableCell>{s.name}</TableCell>
                  <TableCell><Chip label={humanize(s.category)} size="small" variant="outlined" /></TableCell>
                  <TableCell align="right">{formatINR(s.amount)}</TableCell>
                  <TableCell>{humanize(s.billing_cycle)}</TableCell>
                  <TableCell>{formatDate(s.next_billing_date)}</TableCell>
                  <TableCell align="right">{formatINR(s.monthly_cost)}</TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => { setEditing(s); setOpen(true); }}><EditRoundedIcon fontSize="small" /></IconButton>
                    <IconButton size="small" onClick={() => setDeleteTarget(s)}><DeleteRoundedIcon fontSize="small" /></IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <FormDialog
        open={open}
        title={editing ? 'Edit subscription' : 'Add subscription'}
        onClose={() => setOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <RHFTextField control={control} name="name" label="Name" required />
          <RHFSelect control={control} name="category" label="Category" options={subscriptionCategories} />
          <RHFTextField control={control} name="amount" label="Amount (₹)" type="number" required />
          <RHFSelect control={control} name="billing_cycle" label="Billing cycle" options={frequencies} />
          <RHFTextField control={control} name="start_date" label="Start date" type="date" required />
          <RHFTextField control={control} name="next_billing_date" label="Next renewal" type="date" required />
          <RHFSelect control={control} name="payment_method" label="Payment method" options={paymentMethods} />
          <RHFTextField control={control} name="reminder_days" label="Reminder (days before)" type="number" step="1" max="60" />
        </Stack>
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete subscription?"
        message={`Delete "${deleteTarget?.name ?? ''}"?`}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={removeM.isPending}
      />
    </Box>
  );
}
