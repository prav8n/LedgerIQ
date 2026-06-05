import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  Box,
  Button,
  Chip,
  IconButton,
  LinearProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import PaidRoundedIcon from '@mui/icons-material/PaidRounded';

import { PageHeader } from '@/components/PageHeader';
import { FormDialog } from '@/components/FormDialog';
import { RHFTextField } from '@/components/form/RHFTextField';
import { RHFSelect } from '@/components/form/RHFSelect';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { emiHooks, useEmiPay } from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { loanTypes } from '@/constants/enums';
import { formatDate, formatINR, humanize } from '@/utils/format';
import type { EMI, EMIInput } from '@/types/finance';

interface FormValues {
  loan_name: string;
  loan_type: string;
  lender: string;
  principal_amount: string;
  interest_rate: string;
  tenure_months: string;
  emi_amount: string;
  start_date: string;
  next_due_date: string;
}

const today = () => new Date().toISOString().slice(0, 10);
const empty = (): FormValues => ({
  loan_name: '', loan_type: 'personal', lender: '', principal_amount: '',
  interest_rate: '', tenure_months: '', emi_amount: '', start_date: today(), next_due_date: today(),
});

export function EMIsPage() {
  const toast = useToast();
  const { data, isLoading } = emiHooks.useList();
  const createM = emiHooks.useCreate();
  const updateM = emiHooks.useUpdate();
  const removeM = emiHooks.useRemove();
  const payM = useEmiPay();

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<EMI | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<EMI | null>(null);

  const { control, handleSubmit, reset } = useForm<FormValues>({ defaultValues: empty() });

  useEffect(() => {
    if (!open) return;
    reset(
      editing
        ? {
            loan_name: editing.loan_name, loan_type: editing.loan_type, lender: editing.lender ?? '',
            principal_amount: editing.principal_amount, interest_rate: editing.interest_rate,
            tenure_months: String(editing.tenure_months), emi_amount: editing.emi_amount,
            start_date: editing.start_date, next_due_date: editing.next_due_date,
          }
        : empty(),
    );
  }, [open, editing, reset]);

  const onSubmit = handleSubmit(async (v) => {
    const body: EMIInput = {
      loan_name: v.loan_name, loan_type: v.loan_type, lender: v.lender || null,
      principal_amount: Number(v.principal_amount), interest_rate: Number(v.interest_rate),
      tenure_months: Number(v.tenure_months), emi_amount: v.emi_amount ? Number(v.emi_amount) : 0,
      start_date: v.start_date, next_due_date: v.next_due_date,
    };
    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Loan updated' : 'Loan added');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  });

  const pay = async (emi: EMI) => {
    try {
      await payM.mutateAsync(emi.id);
      toast.success('Payment recorded');
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await removeM.mutateAsync(deleteTarget.id);
      toast.success('Loan deleted');
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <PageHeader
        title="EMIs"
        subtitle="Loans and instalments"
        action={
          <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={() => { setEditing(null); setOpen(true); }}>
            Add loan
          </Button>
        }
      />

      {isLoading && <LoadingSkeleton cards={0} rows={5} />}
      {!isLoading && data && data.length === 0 && (
        <EmptyState title="No loans yet" description="Add a loan to track EMIs and outstanding balance." actionLabel="Add loan" onAction={() => { setEditing(null); setOpen(true); }} />
      )}

      {!isLoading && data && data.length > 0 && (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Loan</TableCell>
                <TableCell>Type</TableCell>
                <TableCell align="right">EMI</TableCell>
                <TableCell align="right">Outstanding</TableCell>
                <TableCell>Progress</TableCell>
                <TableCell>Next due</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((emi) => (
                <TableRow key={emi.id} hover>
                  <TableCell>{emi.loan_name}</TableCell>
                  <TableCell><Chip label={humanize(emi.loan_type)} size="small" variant="outlined" /></TableCell>
                  <TableCell align="right">{formatINR(emi.emi_amount)}</TableCell>
                  <TableCell align="right">{formatINR(emi.outstanding)}</TableCell>
                  <TableCell sx={{ minWidth: 140 }}>
                    <LinearProgress variant="determinate" value={Math.min(emi.progress_percent, 100)} sx={{ height: 6, borderRadius: 3, mb: 0.5 }} />
                    <Box component="span" sx={{ fontSize: 12, color: 'text.secondary' }}>
                      {emi.months_paid}/{emi.tenure_months} months
                    </Box>
                  </TableCell>
                  <TableCell>{emi.is_active ? formatDate(emi.next_due_date) : 'Closed'}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Record payment">
                      <span>
                        <IconButton size="small" disabled={!emi.is_active || payM.isPending} onClick={() => void pay(emi)}>
                          <PaidRoundedIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <IconButton size="small" onClick={() => { setEditing(emi); setOpen(true); }}><EditRoundedIcon fontSize="small" /></IconButton>
                    <IconButton size="small" onClick={() => setDeleteTarget(emi)}><DeleteRoundedIcon fontSize="small" /></IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <FormDialog
        open={open}
        title={editing ? 'Edit loan' : 'Add loan'}
        onClose={() => setOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <RHFTextField control={control} name="loan_name" label="Loan name" required />
          <RHFSelect control={control} name="loan_type" label="Loan type" options={loanTypes} />
          <RHFTextField control={control} name="lender" label="Lender" />
          <RHFTextField control={control} name="principal_amount" label="Principal (₹)" type="number" required />
          <RHFTextField control={control} name="interest_rate" label="Interest rate (% p.a.)" type="number" step="0.001" required />
          <RHFTextField control={control} name="tenure_months" label="Tenure (months)" type="number" step="1" min="1" required />
          <RHFTextField control={control} name="emi_amount" label="EMI amount (₹, optional)" type="number" helperText="Leave blank to auto-calculate" />
          <RHFTextField control={control} name="start_date" label="Start date" type="date" required />
          <RHFTextField control={control} name="next_due_date" label="Next due date" type="date" required />
        </Stack>
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete loan?"
        message={`Delete "${deleteTarget?.loan_name ?? ''}"?`}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={removeM.isPending}
      />
    </Box>
  );
}
