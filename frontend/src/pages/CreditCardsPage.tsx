import { useEffect, useState } from 'react';
import { useFieldArray, useForm, useWatch, type Control } from 'react-hook-form';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import AddRoundedIcon from '@mui/icons-material/AddRounded';
import EditRoundedIcon from '@mui/icons-material/EditRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import CreditCardRoundedIcon from '@mui/icons-material/CreditCardRounded';

import { PageHeader } from '@/components/PageHeader';
import { FormDialog } from '@/components/FormDialog';
import { RHFTextField } from '@/components/form/RHFTextField';
import { RHFSelect } from '@/components/form/RHFSelect';
import { RHFSwitch } from '@/components/form/RHFSwitch';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import {
  creditCardHooks,
  useCreateCard,
  useRemoveCard,
  useUpdateCard,
} from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { cardNetworks, rewardAppliesTo, rewardTypes } from '@/constants/enums';
import { formatDate, formatINR, formatPercent, toNumber } from '@/utils/format';
import type {
  CreditCard as Card_,
  CreditCardInput,
  RewardRule,
  RewardRuleInput,
  RuleEarning,
} from '@/types/finance';

// --------------------------------------------------------------- form types
interface RuleForm {
  rule_name: string;
  reward_type: string;
  reward_rate: string;
  point_value: string;
  applies_to: string;
  merchant_match: string;
  category_match: string;
  min_txn_amount: string;
  monthly_cap: string;
  milestone_threshold: string;
  milestone_reward: string;
  notes: string;
}

interface FormValues {
  card_name: string;
  issuer: string;
  network: string;
  last_four: string;
  card_color: string;
  credit_limit: string;
  current_balance: string;
  statement_day: string;
  due_day: string;
  billing_cycle_day: string;
  annual_fee: string;
  fee_waiver_spend_threshold: string;
  is_active: boolean;
  reward_rules: RuleForm[];
}

const num = (s: string): number | undefined => {
  const t = s.trim();
  if (t === '') return undefined;
  const n = Number(t);
  return Number.isFinite(n) ? n : undefined;
};
const numInt = (s: string): number | null => {
  const n = num(s);
  return n === undefined ? null : Math.trunc(n);
};

const emptyRule = (): RuleForm => ({
  rule_name: '',
  reward_type: 'cashback',
  reward_rate: '',
  point_value: '',
  applies_to: 'all',
  merchant_match: '',
  category_match: '',
  min_txn_amount: '',
  monthly_cap: '',
  milestone_threshold: '',
  milestone_reward: '',
  notes: '',
});

const emptyForm = (): FormValues => ({
  card_name: '',
  issuer: '',
  network: 'visa',
  last_four: '',
  card_color: '',
  credit_limit: '',
  current_balance: '0',
  statement_day: '',
  due_day: '',
  billing_cycle_day: '',
  annual_fee: '0',
  fee_waiver_spend_threshold: '',
  is_active: true,
  reward_rules: [],
});

const ruleToForm = (r: RewardRule): RuleForm => ({
  rule_name: r.rule_name,
  reward_type: r.reward_type,
  reward_rate: r.reward_rate ?? '',
  point_value: r.point_value ?? '',
  applies_to: r.applies_to,
  merchant_match: r.merchant_match ?? '',
  category_match: r.category_match ?? '',
  min_txn_amount: r.min_txn_amount ?? '',
  monthly_cap: r.monthly_cap ?? '',
  milestone_threshold: r.milestone_threshold ?? '',
  milestone_reward: r.milestone_reward ?? '',
  notes: r.notes ?? '',
});

const cardToForm = (c: Card_): FormValues => ({
  card_name: c.card_name,
  issuer: c.issuer,
  network: c.network,
  last_four: c.last_four ?? '',
  card_color: c.card_color ?? '',
  credit_limit: c.credit_limit ?? '',
  current_balance: c.current_balance ?? '0',
  statement_day: c.statement_day != null ? String(c.statement_day) : '',
  due_day: c.due_day != null ? String(c.due_day) : '',
  billing_cycle_day: c.billing_cycle_day != null ? String(c.billing_cycle_day) : '',
  annual_fee: c.annual_fee ?? '0',
  fee_waiver_spend_threshold: c.fee_waiver_spend_threshold ?? '',
  is_active: c.is_active,
  reward_rules: c.reward_rules.map(ruleToForm),
});

const toRuleInput = (r: RuleForm): RewardRuleInput => ({
  rule_name: r.rule_name.trim(),
  reward_type: r.reward_type,
  applies_to: r.applies_to,
  reward_rate: num(r.reward_rate) ?? 0,
  point_value: num(r.point_value) ?? null,
  merchant_match: r.merchant_match.trim() || null,
  category_match: r.category_match.trim() || null,
  min_txn_amount: num(r.min_txn_amount) ?? null,
  monthly_cap: num(r.monthly_cap) ?? null,
  milestone_threshold: num(r.milestone_threshold) ?? null,
  milestone_reward: num(r.milestone_reward) ?? null,
  notes: r.notes.trim() || null,
});

function utilizationColor(pct: number): 'success' | 'warning' | 'error' {
  if (pct >= 75) return 'error';
  if (pct >= 40) return 'warning';
  return 'success';
}

function earningText(e: RuleEarning): string {
  if (e.reward_type === 'cashback') return formatINR(e.reward_value_inr);
  const unit = e.reward_type === 'air_miles' ? 'miles' : 'pts';
  const units = toNumber(e.reward_units).toLocaleString('en-IN');
  return `${units} ${unit} · ${formatINR(e.reward_value_inr)}`;
}

// --------------------------------------------------- per-rule form fields
function RuleFields({
  control,
  index,
  onRemove,
}: {
  control: Control<FormValues>;
  index: number;
  onRemove: () => void;
}) {
  const type = useWatch({ control, name: `reward_rules.${index}.reward_type` });
  const appliesTo = useWatch({ control, name: `reward_rules.${index}.applies_to` });
  const isCashback = type === 'cashback';
  const isPoints = type === 'reward_points' || type === 'air_miles';
  const isMilestone = type === 'milestone_bonus';
  const isTxn = isCashback || isPoints;

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1.5}>
        <Typography variant="subtitle2">Rule {index + 1}</Typography>
        <IconButton size="small" aria-label="Remove rule" onClick={onRemove}>
          <DeleteRoundedIcon fontSize="small" />
        </IconButton>
      </Stack>
      <Stack spacing={2}>
        <RHFTextField
          control={control}
          name={`reward_rules.${index}.rule_name`}
          label="Rule name"
          required
        />
        <RHFSelect
          control={control}
          name={`reward_rules.${index}.reward_type`}
          label="Reward type"
          options={rewardTypes}
        />

        {isTxn && (
          <>
            <RHFTextField
              control={control}
              name={`reward_rules.${index}.reward_rate`}
              label={isCashback ? 'Rate (% cashback)' : 'Rate (units per ₹)'}
              type="number"
              required
            />
            {isPoints && (
              <RHFTextField
                control={control}
                name={`reward_rules.${index}.point_value`}
                label="₹ value per point / mile"
                type="number"
                helperText="Used to show the ₹ equivalent"
              />
            )}
            <RHFSelect
              control={control}
              name={`reward_rules.${index}.applies_to`}
              label="Applies to"
              options={rewardAppliesTo}
            />
            {appliesTo === 'merchant_specific' && (
              <RHFTextField
                control={control}
                name={`reward_rules.${index}.merchant_match`}
                label="Merchant (e.g. swiggy)"
              />
            )}
            {appliesTo === 'category_specific' && (
              <RHFTextField
                control={control}
                name={`reward_rules.${index}.category_match`}
                label="Category (e.g. travel)"
              />
            )}
            <Stack direction="row" spacing={2}>
              <RHFTextField
                control={control}
                name={`reward_rules.${index}.min_txn_amount`}
                label="Min txn ₹ (optional)"
                type="number"
              />
              <RHFTextField
                control={control}
                name={`reward_rules.${index}.monthly_cap`}
                label={isCashback ? 'Monthly cap ₹' : 'Monthly cap (units)'}
                type="number"
              />
            </Stack>
          </>
        )}

        {isMilestone && (
          <Stack direction="row" spacing={2}>
            <RHFTextField
              control={control}
              name={`reward_rules.${index}.milestone_threshold`}
              label="Spend threshold ₹"
              type="number"
            />
            <RHFTextField
              control={control}
              name={`reward_rules.${index}.milestone_reward`}
              label="Reward ₹"
              type="number"
            />
          </Stack>
        )}

        <RHFTextField control={control} name={`reward_rules.${index}.notes`} label="Notes" />
      </Stack>
    </Box>
  );
}

// ------------------------------------------------------------- card widget
function CardItem({
  card,
  onEdit,
  onDelete,
}: {
  card: Card_;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const s = card.reward_summary;
  const util = card.utilization_percent;
  const fw = s.fee_waiver;

  return (
    <Card
      sx={{
        height: '100%',
        borderTop: 4,
        borderTopColor: card.card_color || 'primary.main',
        opacity: card.is_active ? 1 : 0.6,
      }}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1.5}>
          <Box minWidth={0}>
            <Typography variant="h6" noWrap>
              {card.card_name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {card.issuer}
              {card.last_four ? ` •••• ${card.last_four}` : ''}
            </Typography>
          </Box>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Chip label={card.network.toUpperCase()} size="small" variant="outlined" />
            <IconButton size="small" aria-label="Edit card" onClick={onEdit}>
              <EditRoundedIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" aria-label="Delete card" onClick={onDelete}>
              <DeleteRoundedIcon fontSize="small" />
            </IconButton>
          </Stack>
        </Stack>

        {!card.is_active && <Chip label="Inactive" size="small" sx={{ mb: 1.5 }} />}

        {/* Balance + utilization */}
        <Stack direction="row" spacing={3} mb={1}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Outstanding
            </Typography>
            <Typography variant="subtitle1" fontWeight={700}>
              {formatINR(card.current_balance)}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Available
            </Typography>
            <Typography variant="subtitle1" fontWeight={700}>
              {formatINR(card.available_credit)}
            </Typography>
          </Box>
        </Stack>
        <Box mb={1.5}>
          <Stack direction="row" justifyContent="space-between" mb={0.5}>
            <Typography variant="caption" color="text.secondary">
              Utilization
            </Typography>
            <Typography variant="caption" fontWeight={700}>
              {formatPercent(util)} of {formatINR(card.credit_limit)}
            </Typography>
          </Stack>
          <LinearProgress
            variant="determinate"
            value={Math.min(util, 100)}
            color={utilizationColor(util)}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Statement / due */}
        {(card.next_statement_date || card.next_due_date) && (
          <Stack direction="row" spacing={3} mb={1.5}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Statement
              </Typography>
              <Typography variant="body2">{formatDate(card.next_statement_date)}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Due
              </Typography>
              <Typography variant="body2">{formatDate(card.next_due_date)}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Amount due
              </Typography>
              <Typography variant="body2" fontWeight={700}>
                {formatINR(card.current_balance)}
              </Typography>
            </Box>
          </Stack>
        )}

        <Divider sx={{ my: 1.5 }} />

        {/* Rewards this month */}
        <Stack direction="row" justifyContent="space-between" alignItems="baseline" mb={0.5}>
          <Typography variant="subtitle2">Rewards · {s.month_label}</Typography>
          <Typography variant="subtitle2" color="success.main">
            {formatINR(s.total_reward_value_inr)}
          </Typography>
        </Stack>
        {s.earnings.length === 0 ? (
          <Typography variant="caption" color="text.secondary">
            No rewards earned yet this month.
          </Typography>
        ) : (
          <Stack spacing={0.5} mb={1}>
            {s.earnings.map((e) => (
              <Stack key={e.rule_id} direction="row" justifyContent="space-between">
                <Typography variant="caption" color="text.secondary" noWrap>
                  {e.rule_name}
                  {e.capped ? ' (capped)' : ''}
                </Typography>
                <Typography variant="caption" fontWeight={700}>
                  {earningText(e)}
                </Typography>
              </Stack>
            ))}
          </Stack>
        )}

        {/* Milestone progress */}
        {s.milestones.map((m) => (
          <Box key={m.rule_id} mt={1}>
            <Stack direction="row" justifyContent="space-between" mb={0.5}>
              <Typography variant="caption" color="text.secondary">
                {m.rule_name}
                {m.met ? ' ✓' : ''}
              </Typography>
              <Typography variant="caption" fontWeight={700}>
                {formatINR(m.progress)} / {formatINR(m.threshold)}
              </Typography>
            </Stack>
            <LinearProgress
              variant="determinate"
              value={Math.min(m.percent, 100)}
              color={m.met ? 'success' : 'primary'}
              sx={{ height: 6, borderRadius: 4 }}
            />
          </Box>
        ))}

        {/* Fee-waiver progress */}
        {fw && (
          <Box mt={1}>
            <Stack direction="row" justifyContent="space-between" mb={0.5}>
              <Typography variant="caption" color="text.secondary">
                Fee waiver {fw.met ? '✓ met' : ''}
              </Typography>
              <Typography variant="caption" fontWeight={700}>
                {formatINR(fw.spent)} / {formatINR(fw.threshold)}
              </Typography>
            </Stack>
            <LinearProgress
              variant="determinate"
              value={Math.min(fw.percent, 100)}
              color={fw.met ? 'success' : 'secondary'}
              sx={{ height: 6, borderRadius: 4 }}
            />
          </Box>
        )}

        {/* Benefits */}
        {s.benefits.length > 0 && (
          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap mt={1.5}>
            {s.benefits.map((b) => (
              <Chip key={b} label={b} size="small" variant="outlined" />
            ))}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}

// ------------------------------------------------------------------- page
export function CreditCardsPage() {
  const toast = useToast();
  const { data, isLoading } = creditCardHooks.useList();
  const createM = useCreateCard();
  const updateM = useUpdateCard();
  const removeM = useRemoveCard();

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Card_ | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Card_ | null>(null);

  const { control, handleSubmit, reset } = useForm<FormValues>({ defaultValues: emptyForm() });
  const { fields, append, remove } = useFieldArray({ control, name: 'reward_rules' });

  useEffect(() => {
    if (!open) return;
    reset(editing ? cardToForm(editing) : emptyForm());
  }, [open, editing, reset]);

  const openAdd = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (card: Card_) => {
    setEditing(card);
    setOpen(true);
  };

  const onSubmit = handleSubmit(async (v) => {
    if (!(Number(v.credit_limit) > 0)) {
      toast.error('Credit limit must be greater than 0');
      return;
    }
    for (const [i, r] of v.reward_rules.entries()) {
      const rate = num(r.reward_rate);
      if (rate !== undefined && rate < 0) {
        toast.error(`Rule ${i + 1}: rate cannot be negative`);
        return;
      }
      if (r.reward_type === 'cashback' && rate !== undefined && rate > 100) {
        toast.error(`Rule ${i + 1}: cashback percent cannot exceed 100`);
        return;
      }
    }

    const body: CreditCardInput = {
      card_name: v.card_name.trim(),
      issuer: v.issuer.trim(),
      network: v.network,
      last_four: v.last_four.trim() || null,
      card_color: v.card_color.trim() || null,
      credit_limit: Number(v.credit_limit),
      current_balance: num(v.current_balance) ?? 0,
      statement_day: numInt(v.statement_day),
      due_day: numInt(v.due_day),
      billing_cycle_day: numInt(v.billing_cycle_day),
      annual_fee: num(v.annual_fee) ?? 0,
      fee_waiver_spend_threshold: num(v.fee_waiver_spend_threshold) ?? null,
      is_active: v.is_active,
      reward_rules: v.reward_rules.map(toRuleInput),
    };

    try {
      if (editing) await updateM.mutateAsync({ id: editing.id, body });
      else await createM.mutateAsync(body);
      toast.success(editing ? 'Card updated' : 'Card added');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  });

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await removeM.mutateAsync(deleteTarget.id);
      toast.success('Card deleted');
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <PageHeader
        title="Credit Cards"
        subtitle="Track limits, dues and rewards across all your cards"
        action={
          <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={openAdd}>
            Add card
          </Button>
        }
      />

      {isLoading && <LoadingSkeleton cards={0} rows={5} />}

      {!isLoading && data && data.length === 0 && (
        <EmptyState
          icon={<CreditCardRoundedIcon />}
          title="No credit cards yet"
          description="Add a card and its reward rules to track spend, dues and rewards."
          actionLabel="Add card"
          onAction={openAdd}
        />
      )}

      {!isLoading && data && data.length > 0 && (
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr', lg: 'repeat(3, 1fr)' },
          }}
        >
          {data.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              onEdit={() => openEdit(card)}
              onDelete={() => setDeleteTarget(card)}
            />
          ))}
        </Box>
      )}

      <FormDialog
        open={open}
        title={editing ? 'Edit card' : 'Add card'}
        onClose={() => setOpen(false)}
        onSubmit={onSubmit}
        submitting={createM.isPending || updateM.isPending}
        maxWidth="md"
      >
        <Stack spacing={2} mt={1}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <RHFTextField control={control} name="card_name" label="Card name" required autoFocus />
            <RHFTextField control={control} name="issuer" label="Issuer" required />
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <RHFSelect control={control} name="network" label="Network" options={cardNetworks} />
            <RHFTextField control={control} name="last_four" label="Last 4 digits" />
            <RHFTextField control={control} name="card_color" label="Color (hex, optional)" />
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <RHFTextField
              control={control}
              name="credit_limit"
              label="Credit limit (₹)"
              type="number"
              required
            />
            <RHFTextField
              control={control}
              name="current_balance"
              label="Outstanding (₹)"
              type="number"
            />
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <RHFTextField
              control={control}
              name="statement_day"
              label="Statement day"
              type="number"
              min="1"
              max="31"
            />
            <RHFTextField
              control={control}
              name="due_day"
              label="Due day"
              type="number"
              min="1"
              max="31"
            />
            <RHFTextField
              control={control}
              name="billing_cycle_day"
              label="Cycle day"
              type="number"
              min="1"
              max="31"
            />
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <RHFTextField control={control} name="annual_fee" label="Annual fee (₹)" type="number" />
            <RHFTextField
              control={control}
              name="fee_waiver_spend_threshold"
              label="Fee waiver spend (₹, optional)"
              type="number"
            />
          </Stack>
          <RHFSwitch control={control} name="is_active" label="Active" />

          <Divider />
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="subtitle1">Reward rules</Typography>
            <Button size="small" startIcon={<AddRoundedIcon />} onClick={() => append(emptyRule())}>
              Add rule
            </Button>
          </Stack>
          {fields.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              No reward rules yet. Add cashback, points, miles, milestones, fee waivers and more.
            </Typography>
          )}
          {fields.map((field, index) => (
            <RuleFields
              key={field.id}
              control={control}
              index={index}
              onRemove={() => remove(index)}
            />
          ))}
        </Stack>
      </FormDialog>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete card?"
        message={`Delete "${deleteTarget?.card_name ?? ''}" and all its reward rules? This cannot be undone.`}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDeleteTarget(null)}
        busy={removeM.isPending}
      />
    </Box>
  );
}
