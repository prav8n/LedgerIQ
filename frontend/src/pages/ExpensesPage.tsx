import { useEffect, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
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
  TableSortLabel,
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
import { creditCardHooks } from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { expenseCategories, paymentMethods } from '@/constants/enums';
import { formatDate, formatINR, humanize } from '@/utils/format';
import type { Expense, ExpenseInput, ExpenseSort, SortOrder } from '@/types/expense';

interface FormValues {
  amount: string;
  transaction_date: string;
  category: string; // '' => auto-categorize
  merchant: string;
  description: string;
  payment_method: string;
  credit_card_id: string; // '' => none
  reward_rule_id: string; // '' => auto (best match)
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
  credit_card_id: '',
  reward_rule_id: '',
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
  const [ccFilter, setCcFilter] = useState(''); // credit_card_id ('' = all)
  const [ruleFilter, setRuleFilter] = useState(''); // rule_id ('' = all)
  const [sort, setSort] = useState<ExpenseSort>('date');
  const [order, setOrder] = useState<SortOrder>('desc');

  const periodRange = periodFilter ? periodBounds(periodFilter) : null;
  const filters = {
    page: page + 1,
    size,
    sort,
    order,
    ...(q ? { q } : {}),
    ...(category ? { category } : {}),
    ...(ccFilter ? { credit_card_id: Number(ccFilter) } : {}),
    ...(ruleFilter ? { rule_id: Number(ruleFilter) } : {}),
    ...(periodRange ? { date_from: periodRange.start, date_to: periodRange.end } : {}),
  };
  const { data, isLoading, isError, refetch } = useExpenses(filters);

  const toggleSort = (field: ExpenseSort) => {
    setPage(0);
    if (sort === field) {
      setOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
    } else {
      setSort(field);
      setOrder(field === 'merchant' || field === 'category' ? 'asc' : 'desc');
    }
  };

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

  // Credit cards, so a card-paid expense can be linked to the card that earns
  // the cashback / reward points.
  const { data: cards } = creditCardHooks.useList();
  const cardOptions = (cards ?? []).map((c) => ({ value: String(c.id), label: c.card_name }));

  // Maps + options for the Card / Reward-rule columns and filters.
  const cardNameById = new Map((cards ?? []).map((c) => [c.id, c.card_name]));
  const ruleNameById = new Map(
    (cards ?? []).flatMap((c) => c.reward_rules.map((r) => [r.id, r.rule_name] as const)),
  );
  const filterRuleOptions = (cards ?? [])
    .filter((c) => !ccFilter || String(c.id) === ccFilter)
    .flatMap((c) =>
      c.reward_rules.map((r) => ({
        value: String(r.id),
        label: ccFilter ? r.rule_name : `${c.card_name} · ${r.rule_name}`,
      })),
    );

  const paymentMethod = useWatch({ control, name: 'payment_method' });
  const creditCardId = useWatch({ control, name: 'credit_card_id' });

  // Per-transaction reward rules of the chosen card, so the user can force one
  // (e.g. "10% PhonePe" vs the generic "1% UPI") when the engine can't tell.
  const TXN_REWARD = new Set(['cashback', 'reward_points', 'air_miles']);
  const selectedCard = (cards ?? []).find((c) => String(c.id) === creditCardId);
  const ruleOptions = (selectedCard?.reward_rules ?? [])
    .filter((r) => TXN_REWARD.has(r.reward_type))
    .map((r) => ({ value: String(r.id), label: r.rule_name }));
  const validRuleIds = new Set(ruleOptions.map((o) => o.value));

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
            credit_card_id:
              editing.credit_card_id != null ? String(editing.credit_card_id) : '',
            reward_rule_id:
              editing.reward_rule_id != null ? String(editing.reward_rule_id) : '',
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
      credit_card_id:
        values.payment_method === 'credit_card' && values.credit_card_id
          ? Number(values.credit_card_id)
          : null,
      reward_rule_id:
        values.payment_method === 'credit_card' &&
        values.reward_rule_id &&
        validRuleIds.has(values.reward_rule_id)
          ? Number(values.reward_rule_id)
          : null,
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
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} mb={2} useFlexGap flexWrap="wrap">
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
        {cardOptions.length > 0 && (
          <TextField
            select
            size="small"
            label="Credit card"
            value={ccFilter}
            onChange={(e) => {
              setPage(0);
              setCcFilter(e.target.value);
              setRuleFilter(''); // rule list depends on the card
            }}
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="">All cards</MenuItem>
            {cardOptions.map((o) => (
              <MenuItem key={o.value} value={o.value}>
                {o.label}
              </MenuItem>
            ))}
          </TextField>
        )}
        {filterRuleOptions.length > 0 && (
          <TextField
            select
            size="small"
            label="Reward rule"
            value={ruleFilter}
            onChange={(e) => {
              setPage(0);
              setRuleFilter(e.target.value);
            }}
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All rules</MenuItem>
            {filterRuleOptions.map((o) => (
              <MenuItem key={o.value} value={o.value}>
                {o.label}
              </MenuItem>
            ))}
          </TextField>
        )}
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
                <TableCell sortDirection={sort === 'date' ? order : false}>
                  <TableSortLabel
                    active={sort === 'date'}
                    direction={sort === 'date' ? order : 'asc'}
                    onClick={() => toggleSort('date')}
                  >
                    Date
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={sort === 'merchant' ? order : false}>
                  <TableSortLabel
                    active={sort === 'merchant'}
                    direction={sort === 'merchant' ? order : 'asc'}
                    onClick={() => toggleSort('merchant')}
                  >
                    Merchant
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={sort === 'category' ? order : false}>
                  <TableSortLabel
                    active={sort === 'category'}
                    direction={sort === 'category' ? order : 'asc'}
                    onClick={() => toggleSort('category')}
                  >
                    Category
                  </TableSortLabel>
                </TableCell>
                <TableCell>Payment</TableCell>
                <TableCell>Card / Rule</TableCell>
                <TableCell align="right" sortDirection={sort === 'amount' ? order : false}>
                  <TableSortLabel
                    active={sort === 'amount'}
                    direction={sort === 'amount' ? order : 'asc'}
                    onClick={() => toggleSort('amount')}
                  >
                    Amount
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right" sortDirection={sort === 'cashback' ? order : false}>
                  <TableSortLabel
                    active={sort === 'cashback'}
                    direction={sort === 'cashback' ? order : 'asc'}
                    onClick={() => toggleSort('cashback')}
                  >
                    Cashback
                  </TableSortLabel>
                </TableCell>
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
                  <TableCell>
                    {e.credit_card_id != null ? (
                      <>
                        {cardNameById.get(e.credit_card_id) ?? 'Card'}
                        {e.cashback_rule && ruleNameById.has(Number(e.cashback_rule)) ? (
                          <Box
                            component="span"
                            sx={{ display: 'block', color: 'text.secondary', fontSize: 12 }}
                          >
                            {ruleNameById.get(Number(e.cashback_rule))}
                          </Box>
                        ) : null}
                      </>
                    ) : (
                      '—'
                    )}
                  </TableCell>
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
          {paymentMethod === 'credit_card' && (
            <RHFSelect
              control={control}
              name="credit_card_id"
              label="Credit card"
              options={cardOptions}
              emptyLabel={cardOptions.length ? 'No card' : 'Add a card first'}
            />
          )}
          {paymentMethod === 'credit_card' && ruleOptions.length > 0 && (
            <RHFSelect
              control={control}
              name="reward_rule_id"
              label="Reward rule"
              options={ruleOptions}
              emptyLabel="Auto (best match)"
            />
          )}
          <Stack direction="row" spacing={2}>
            <RHFSwitch
              control={control}
              name="is_online"
              label="Online"
              info={
                'Was this an online / e-commerce purchase?\n\n' +
                'It only affects credit-card reward rules that apply to online spend ' +
                '(e.g. “5% cashback online”). Leave it OFF for in-store or cash payments — ' +
                'for cash it has no effect.'
              }
            />
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
