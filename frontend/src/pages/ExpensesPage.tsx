import { useEffect, useState } from 'react';
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
  Tooltip,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import UploadFileRoundedIcon from '@mui/icons-material/UploadFileRounded';
import CalendarMonthRoundedIcon from '@mui/icons-material/CalendarMonthRounded';

import { PageHeader } from '@/components/PageHeader';
import { PeriodSelector } from '@/components/PeriodSelector';
import { defaultPeriod, periodBounds, type PeriodState } from '@/utils/period';
import { FormDialog } from '@/components/FormDialog';
import { RHFTextField } from '@/components/form/RHFTextField';
import { RHFSelect } from '@/components/form/RHFSelect';
import { RHFSwitch } from '@/components/form/RHFSwitch';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { ImportDialog } from '@/components/ImportDialog';
import {
  useCreateExpense,
  useDeleteExpense,
  useExpenses,
  useUpdateExpense,
} from '@/hooks/useExpenses';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { expenseCategories, paymentMethods } from '@/constants/enums';
import { formatDate, formatINR, humanize } from '@/utils/format';
import type { Expense, ExpenseInput } from '@/types/expense';

interface FormValues {
  amount: string;
  transaction_date: string;
  category: string; // '' => auto-categorize
  merchant: string;
  description: string;
  payment_method: string;
  is_online: boolean;
  is_recurring: boolean;
}

const today = () => new Date().toISOString().slice(0, 10);

const emptyForm = (): FormValues => ({
  amount: '',
  transaction_date: today(),
  category: '',
  merchant: '',
  description: '',
  payment_method: 'upi',
  is_online: false,
  is_recurring: false,
});

export function ExpensesPage() {
  const toast = useToast();
  const [page, setPage] = useState(0); // zero-based for MUI
  const [size, setSize] = useState(20);
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  // null = all time; otherwise scope to the selected period (month/quarter/year/FY).
  const [periodFilter, setPeriodFilter] = useState<PeriodState | null>(null);

  const periodRange = periodFilter ? periodBounds(periodFilter) : null;
  const filters = {
    page: page + 1,
    size,
    ...(q ? { q } : {}),
    ...(category ? { category } : {}),
    ...(periodRange ? { date_from: periodRange.start, date_to: periodRange.end } : {}),
  };
  const { data, isLoading, isError, refetch } = useExpenses(filters);

  const createM = useCreateExpense();
  const updateM = useUpdateExpense();
  const deleteM = useDeleteExpense();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Expense | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Expense | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: emptyForm(),
  });

  useEffect(() => {
    if (!formOpen) return;
    reset(
      editing
        ? {
            amount: editing.amount,
            transaction_date: editing.transaction_date,
            category: editing.category,
            merchant: editing.merchant ?? '',
            description: editing.description ?? '',
            payment_method: editing.payment_method,
            is_online: editing.is_online,
            is_recurring: editing.is_recurring,
          }
        : emptyForm(),
    );
  }, [formOpen, editing, reset]);

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };
  const openEdit = (e: Expense) => {
    setEditing(e);
    setFormOpen(true);
  };

  const onSubmit = handleSubmit(async (values) => {
    const body: ExpenseInput = {
      amount: Number(values.amount),
      transaction_date: values.transaction_date,
      category: values.category || null,
      merchant: values.merchant || null,
      description: values.description || null,
      payment_method: values.payment_method,
      is_online: values.is_online,
      is_recurring: values.is_recurring,
    };
    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Expense updated' : 'Expense added');
      setFormOpen(false);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  });

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteM.mutateAsync(deleteTarget.id);
      toast.success('Expense deleted');
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <PageHeader
        title="Expenses"
        subtitle="Every transaction, categorized"
        action={
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<UploadFileRoundedIcon />}
              onClick={() => setImportOpen(true)}
            >
              Import
            </Button>
            <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={openCreate}>
              Add
            </Button>
          </Stack>
        }
      />

      {/* Filters */}
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} mb={2}>
        <TextField
          size="small"
          label="Search merchant / description"
          value={q}
          onChange={(e) => {
            setPage(0);
            setQ(e.target.value);
          }}
          sx={{ flex: 1 }}
        />
        <TextField
          select
          size="small"
          label="Category"
          value={category}
          onChange={(e) => {
            setPage(0);
            setCategory(e.target.value);
          }}
          sx={{ minWidth: 180 }}
        >
          <MenuItem value="">All categories</MenuItem>
          {expenseCategories.map((c) => (
            <MenuItem key={c.value} value={c.value}>
              {c.label}
            </MenuItem>
          ))}
        </TextField>
        {periodFilter ? (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            <PeriodSelector
              value={periodFilter}
              onChange={(p) => {
                setPage(0);
                setPeriodFilter(p);
              }}
            />
            <Button
              size="small"
              onClick={() => {
                setPage(0);
                setPeriodFilter(null);
              }}
            >
              All time
            </Button>
          </Stack>
        ) : (
          <Button
            size="small"
            variant="outlined"
            startIcon={<CalendarMonthRoundedIcon />}
            onClick={() => {
              setPage(0);
              setPeriodFilter(defaultPeriod('monthly'));
            }}
          >
            Filter by period
          </Button>
        )}
      </Stack>

      {isLoading && <LoadingSkeleton cards={0} rows={6} />}
      {!isLoading && (isError || !data) && (
        <EmptyState title="Couldn't load expenses" actionLabel="Retry" onAction={() => void refetch()} />
      )}
      {!isLoading && data && data.items.length === 0 && (
        <EmptyState
          title="No expenses yet"
          description="Add your first expense or import a statement."
          actionLabel="Add expense"
          onAction={openCreate}
        />
      )}

      {!isLoading && data && data.items.length > 0 && (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Merchant</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Payment</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell align="right">Cashback</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.items.map((e) => (
                <TableRow key={e.id} hover>
                  <TableCell>{formatDate(e.transaction_date)}</TableCell>
                  <TableCell>{e.merchant ?? '—'}</TableCell>
                  <TableCell>
                    <Chip label={humanize(e.category)} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>{humanize(e.payment_method)}</TableCell>
                  <TableCell align="right">{formatINR(e.amount)}</TableCell>
                  <TableCell align="right">
                    {Number(e.cashback_amount) > 0 ? (
                      <Box component="span" sx={{ color: 'success.main' }}>
                        {formatINR(e.cashback_amount)}
                      </Box>
                    ) : (
                      '—'
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => openEdit(e)}>
                        <EditRoundedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => setDeleteTarget(e)}>
                        <DeleteRoundedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <TablePagination
            component="div"
            count={data.total}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={size}
            onRowsPerPageChange={(e) => {
              setSize(Number(e.target.value));
              setPage(0);
            }}
            rowsPerPageOptions={[20, 50, 100]}
          />
        </TableContainer>
      )}

      {/* Add / edit form */}
      <FormDialog
        open={formOpen}
        title={editing ? 'Edit expense' : 'Add expense'}
        onClose={() => setFormOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <RHFTextField control={control} name="amount" label="Amount (₹)" type="number" required />
          <RHFTextField control={control} name="transaction_date" label="Date" type="date" required />
          <RHFSelect control={control} name="category" label="Category" options={expenseCategories} emptyLabel="Auto-categorize" />
          <RHFTextField control={control} name="merchant" label="Merchant" />
          <RHFTextField control={control} name="description" label="Description" />
          <RHFSelect control={control} name="payment_method" label="Payment method" options={paymentMethods} />
          <Stack direction="row" spacing={2}>
            <RHFSwitch control={control} name="is_online" label="Online" />
            <RHFSwitch control={control} name="is_recurring" label="Recurring" />
          </Stack>
        </Stack>
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete expense?"
        message={`Delete this ${deleteTarget ? formatINR(deleteTarget.amount) : ''} expense? This cannot be undone.`}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={deleteM.isPending}
      />

      <ImportDialog open={importOpen} onClose={() => setImportOpen(false)} />
    </Box>
  );
}
