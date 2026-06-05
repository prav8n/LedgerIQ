import { useEffect, useState } from 'react';
import type { ChangeEvent } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AddPhotoAlternateRoundedIcon from '@mui/icons-material/CameraAltRounded';

import { PageHeader } from '@/components/PageHeader';
import { FormDialog } from '@/components/FormDialog';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { KpiCard } from '@/components/dashboard/KpiCard';
import {
  useNetWorthCurrent,
  useNetWorthHistory,
  useNetWorthSnapshot,
} from '@/hooks/financeHooks';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { formatDate, formatINR } from '@/utils/format';
import type { NetWorthSnapshotInput } from '@/types/finance';

interface ManualForm {
  cash: string;
  property_value: string;
  other_assets: string;
  other_liabilities: string;
}

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <Stack direction="row" justifyContent="space-between">
      <Typography variant="body2" fontWeight={bold ? 700 : 400} color={bold ? 'text.primary' : 'text.secondary'}>
        {label}
      </Typography>
      <Typography variant="body2" fontWeight={bold ? 700 : 500}>
        {value}
      </Typography>
    </Stack>
  );
}

export function NetWorthPage() {
  const toast = useToast();
  const current = useNetWorthCurrent();
  const history = useNetWorthHistory();
  const snapshotM = useNetWorthSnapshot();

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ManualForm>({ cash: '0', property_value: '0', other_assets: '0', other_liabilities: '0' });

  useEffect(() => {
    if (open && current.data) {
      setForm({
        cash: current.data.cash,
        property_value: current.data.property_value,
        other_assets: current.data.other_assets,
        other_liabilities: current.data.other_liabilities,
      });
    }
  }, [open, current.data]);

  const setField = (k: keyof ManualForm) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const saveSnapshot = async () => {
    const body: NetWorthSnapshotInput = {
      cash: Number(form.cash),
      property_value: Number(form.property_value),
      other_assets: Number(form.other_assets),
      other_liabilities: Number(form.other_liabilities),
    };
    try {
      await snapshotM.mutateAsync(body);
      toast.success('Snapshot saved');
      setOpen(false);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  };

  const nw = current.data;

  return (
    <Box>
      <PageHeader
        title="Net Worth"
        subtitle="Assets minus liabilities"
        action={
          <Button variant="contained" startIcon={<AddPhotoAlternateRoundedIcon />} onClick={() => setOpen(true)}>
            Save snapshot
          </Button>
        }
      />

      {current.isLoading && <LoadingSkeleton cards={3} rows={2} />}

      {nw && (
        <>
          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, mb: 3 }}>
            <KpiCard title="Net Worth" value={formatINR(nw.net_worth)} accent={Number(nw.net_worth) >= 0 ? 'success.main' : 'error.main'} />
            <KpiCard title="Total Assets" value={formatINR(nw.total_assets)} accent="primary.main" />
            <KpiCard title="Total Liabilities" value={formatINR(nw.total_liabilities)} accent="warning.main" />
          </Box>

          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, mb: 3 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={1.5}>Assets</Typography>
                <Stack spacing={1}>
                  <Row label="Cash" value={formatINR(nw.cash)} />
                  <Row label="Investments" value={formatINR(nw.investments_value)} />
                  <Row label="Property" value={formatINR(nw.property_value)} />
                  <Row label="Other assets" value={formatINR(nw.other_assets)} />
                  <Divider />
                  <Row label="Total assets" value={formatINR(nw.total_assets)} bold />
                </Stack>
              </CardContent>
            </Card>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={1.5}>Liabilities</Typography>
                <Stack spacing={1}>
                  <Row label="Credit card debt" value={formatINR(nw.credit_card_debt)} />
                  <Row label="Loans outstanding" value={formatINR(nw.loans_debt)} />
                  <Row label="Other liabilities" value={formatINR(nw.other_liabilities)} />
                  <Divider />
                  <Row label="Total liabilities" value={formatINR(nw.total_liabilities)} bold />
                </Stack>
              </CardContent>
            </Card>
          </Box>
        </>
      )}

      {history.data && history.data.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" mb={1.5}>History</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell align="right">Assets</TableCell>
                  <TableCell align="right">Liabilities</TableCell>
                  <TableCell align="right">Net Worth</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.data.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell>{formatDate(s.snapshot_date)}</TableCell>
                    <TableCell align="right">{formatINR(s.total_assets)}</TableCell>
                    <TableCell align="right">{formatINR(s.total_liabilities)}</TableCell>
                    <TableCell align="right">{formatINR(s.net_worth)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <FormDialog
        open={open}
        title="Save net-worth snapshot"
        onClose={() => setOpen(false)}
        onSubmit={() => void saveSnapshot()}
        submitting={snapshotM.isPending}
      >
        <Stack spacing={2} mt={1}>
          <Typography variant="body2" color="text.secondary">
            Investments, card debt and loan balances are pulled automatically. Enter the rest:
          </Typography>
          <TextField label="Cash & bank (₹)" type="number" value={form.cash} onChange={setField('cash')} />
          <TextField label="Property (₹)" type="number" value={form.property_value} onChange={setField('property_value')} />
          <TextField label="Other assets (₹)" type="number" value={form.other_assets} onChange={setField('other_assets')} />
          <TextField label="Other liabilities (₹)" type="number" value={form.other_liabilities} onChange={setField('other_liabilities')} />
        </Stack>
      </FormDialog>
    </Box>
  );
}
