import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  LinearProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import SavingsRoundedIcon from '@mui/icons-material/SavingsRounded';

import { PageHeader } from '@/components/PageHeader';
import { FormDialog } from '@/components/FormDialog';
import { RHFTextField } from '@/components/form/RHFTextField';
import { RHFSelect } from '@/components/form/RHFSelect';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { goalHooks, useGoalContribute } from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { goalCategories, priorities } from '@/constants/enums';
import { formatDate, formatINR, formatPercent, humanize } from '@/utils/format';
import type { Goal, GoalInput } from '@/types/finance';

interface FormValues {
  name: string;
  category: string;
  target_amount: string;
  current_amount: string;
  monthly_contribution: string;
  target_date: string;
  priority: string;
}

const empty = (): FormValues => ({
  name: '', category: 'other', target_amount: '', current_amount: '0',
  monthly_contribution: '0', target_date: '', priority: 'medium',
});

export function GoalsPage() {
  const toast = useToast();
  const { data, isLoading } = goalHooks.useList();
  const createM = goalHooks.useCreate();
  const updateM = goalHooks.useUpdate();
  const removeM = goalHooks.useRemove();
  const contributeM = useGoalContribute();

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Goal | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Goal | null>(null);
  const [contribGoal, setContribGoal] = useState<Goal | null>(null);
  const [contribAmount, setContribAmount] = useState('');

  const { control, handleSubmit, reset } = useForm<FormValues>({ defaultValues: empty() });

  useEffect(() => {
    if (!open) return;
    reset(
      editing
        ? {
            name: editing.name, category: editing.category, target_amount: editing.target_amount,
            current_amount: editing.current_amount, monthly_contribution: editing.monthly_contribution,
            target_date: editing.target_date ?? '', priority: editing.priority,
          }
        : empty(),
    );
  }, [open, editing, reset]);

  const onSubmit = handleSubmit(async (v) => {
    const body: GoalInput = {
      name: v.name, category: v.category, target_amount: Number(v.target_amount),
      current_amount: Number(v.current_amount), monthly_contribution: Number(v.monthly_contribution),
      target_date: v.target_date || null, priority: v.priority,
    };
    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Goal updated' : 'Goal created');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  });

  const doContribute = async () => {
    if (!contribGoal || !contribAmount) return;
    try {
      await contributeM.mutateAsync({ id: contribGoal.id, amount: Number(contribAmount) });
      toast.success('Contribution added');
      setContribGoal(null);
      setContribAmount('');
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await removeM.mutateAsync(deleteTarget.id);
      toast.success('Goal deleted');
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <PageHeader
        title="Goals"
        subtitle="Save towards what matters"
        action={
          <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={() => { setEditing(null); setOpen(true); }}>
            Add goal
          </Button>
        }
      />

      {isLoading && <LoadingSkeleton cards={3} rows={0} />}
      {!isLoading && data && data.length === 0 && (
        <EmptyState title="No goals yet" description="Set a savings goal and track your progress." actionLabel="Add goal" onAction={() => { setEditing(null); setOpen(true); }} />
      )}

      {!isLoading && data && data.length > 0 && (
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' } }}>
          {data.map((g) => (
            <Card key={g.id}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
                  <Box>
                    <Typography variant="h6">{g.name}</Typography>
                    <Chip label={humanize(g.status)} size="small" color={g.status === 'completed' ? 'success' : 'default'} sx={{ mt: 0.5 }} />
                  </Box>
                  <Box>
                    <IconButton size="small" onClick={() => { setEditing(g); setOpen(true); }}><EditRoundedIcon fontSize="small" /></IconButton>
                    <IconButton size="small" onClick={() => setDeleteTarget(g)}><DeleteRoundedIcon fontSize="small" /></IconButton>
                  </Box>
                </Stack>
                <Typography variant="h5" fontWeight={800}>
                  {formatINR(g.current_amount)} <Typography component="span" variant="body2" color="text.secondary">/ {formatINR(g.target_amount)}</Typography>
                </Typography>
                <LinearProgress variant="determinate" value={Math.min(g.progress_percent, 100)} sx={{ height: 8, borderRadius: 4, my: 1 }} />
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">{formatPercent(g.progress_percent)} · {formatINR(g.remaining)} left</Typography>
                  <Typography variant="caption" color="text.secondary">{g.target_date ? `by ${formatDate(g.target_date)}` : ''}</Typography>
                </Stack>
                {Number(g.required_monthly_contribution) > 0 && (
                  <Typography variant="caption" color="text.secondary" display="block" mt={0.5}>
                    Need {formatINR(g.required_monthly_contribution)}/mo to stay on track
                  </Typography>
                )}
                <Button size="small" startIcon={<SavingsRoundedIcon />} sx={{ mt: 1 }} onClick={() => { setContribGoal(g); setContribAmount(''); }}>
                  Contribute
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      <FormDialog
        open={open}
        title={editing ? 'Edit goal' : 'Add goal'}
        onClose={() => setOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <RHFTextField control={control} name="name" label="Name" required />
          <RHFSelect control={control} name="category" label="Category" options={goalCategories} />
          <RHFTextField control={control} name="target_amount" label="Target amount (₹)" type="number" required />
          <RHFTextField control={control} name="current_amount" label="Current amount (₹)" type="number" />
          <RHFTextField control={control} name="monthly_contribution" label="Monthly contribution (₹)" type="number" />
          <RHFTextField control={control} name="target_date" label="Target date" type="date" />
          <RHFSelect control={control} name="priority" label="Priority" options={priorities} />
        </Stack>
      </FormDialog>

      <FormDialog
        open={Boolean(contribGoal)}
        title={`Contribute to ${contribGoal?.name ?? ''}`}
        onClose={() => setContribGoal(null)}
        onSubmit={() => void doContribute()}
        submitting={contributeM.isPending}
        submitLabel="Add"
        maxWidth="xs"
      >
        <TextField
          autoFocus
          fullWidth
          label="Amount (₹)"
          type="number"
          inputProps={{ step: '0.01', min: '0' }}
          value={contribAmount}
          onChange={(e) => setContribAmount(e.target.value)}
          sx={{ mt: 1 }}
        />
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete goal?"
        message={`Delete "${deleteTarget?.name ?? ''}"?`}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={removeM.isPending}
      />
    </Box>
  );
}
