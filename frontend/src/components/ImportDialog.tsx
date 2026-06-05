import { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import UploadFileRoundedIcon from '@mui/icons-material/UploadFileRounded';
import { importService } from '@/services/importService';
import { getErrorMessage } from '@/services/api';
import { useToast } from '@/hooks/useToast';
import { humanize } from '@/utils/format';
import type { ImportField, ImportMapping, ImportPreview, ImportResult } from '@/types/import';

const FIELDS: { key: ImportField; required: boolean }[] = [
  { key: 'transaction_date', required: true },
  { key: 'amount', required: true },
  { key: 'merchant', required: false },
  { key: 'description', required: false },
  { key: 'category', required: false },
  { key: 'payment_method', required: false },
];

const NONE = '__none__';

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ImportDialog({ open, onClose }: Props) {
  const qc = useQueryClient();
  const toast = useToast();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [mapping, setMapping] = useState<ImportMapping | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setFile(null);
    setPreview(null);
    setMapping(null);
    setResult(null);
    setBusy(false);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const onFile = async (selected: File) => {
    setFile(selected);
    setResult(null);
    setBusy(true);
    try {
      const pv = await importService.preview(selected);
      setPreview(pv);
      setMapping(pv.suggested_mapping);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Could not read the file'));
      reset();
    } finally {
      setBusy(false);
    }
  };

  const setField = (field: ImportField, header: string) => {
    setMapping((m) => (m ? { ...m, [field]: header === NONE ? null : header } : m));
  };

  const doImport = async () => {
    if (!file || !mapping) return;
    setBusy(true);
    try {
      const res = await importService.commit(file, mapping);
      setResult(res);
      void qc.invalidateQueries({ queryKey: ['expenses'] });
      void qc.invalidateQueries({ queryKey: ['dashboard'] });
      toast.success(`Imported ${res.created} expense(s)`);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Import failed'));
    } finally {
      setBusy(false);
    }
  };

  const mappingValid = Boolean(mapping?.transaction_date && mapping?.amount);

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Import expenses (CSV / XLSX)</DialogTitle>
      <DialogContent dividers>
        {/* Step 1: file */}
        {!preview && !result && (
          <Stack alignItems="center" spacing={2} py={4}>
            <UploadFileRoundedIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
            <Typography variant="body2" color="text.secondary" textAlign="center">
              Upload a bank/credit-card statement. Columns are auto-mapped — you can adjust them.
            </Typography>
            <Button variant="contained" component="label" disabled={busy}>
              {busy ? 'Reading…' : 'Choose file'}
              <input
                ref={fileRef}
                type="file"
                accept=".csv,.xlsx,.xlsm,.txt"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void onFile(f);
                }}
              />
            </Button>
          </Stack>
        )}

        {/* Step 2: map + preview */}
        {preview && !result && mapping && (
          <Stack spacing={2}>
            <Alert severity="info">
              {preview.total_rows} row(s) found in <strong>{file?.name}</strong>. Map your columns:
            </Alert>
            <Box
              sx={{
                display: 'grid',
                gap: 2,
                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
              }}
            >
              {FIELDS.map(({ key, required }) => (
                <TextField
                  key={key}
                  select
                  size="small"
                  label={`${humanize(key)}${required ? ' *' : ''}`}
                  value={mapping[key] ?? NONE}
                  onChange={(e) => setField(key, e.target.value)}
                  error={required && !mapping[key]}
                >
                  <MenuItem value={NONE}>— none —</MenuItem>
                  {preview.headers.map((h) => (
                    <MenuItem key={h} value={h}>
                      {h}
                    </MenuItem>
                  ))}
                </TextField>
              ))}
            </Box>

            <Typography variant="subtitle2">Preview</Typography>
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {preview.headers.map((h) => (
                      <TableCell key={h}>{h}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {preview.sample_rows.map((row, i) => (
                    <TableRow key={i}>
                      {preview.headers.map((h) => (
                        <TableCell key={h}>{row[h]}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Stack>
        )}

        {/* Step 3: result */}
        {result && (
          <Stack spacing={2} py={2}>
            <Alert severity={result.created > 0 ? 'success' : 'warning'}>
              Imported <strong>{result.created}</strong> expense(s), skipped{' '}
              <strong>{result.skipped}</strong>.
            </Alert>
            {result.errors.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Skipped rows
                </Typography>
                <Stack spacing={0.5} sx={{ maxHeight: 200, overflowY: 'auto' }}>
                  {result.errors.map((err) => (
                    <Typography key={err.row} variant="caption" color="text.secondary">
                      Row {err.row}: {err.error}
                    </Typography>
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{result ? 'Done' : 'Cancel'}</Button>
        {preview && !result && (
          <Button variant="contained" onClick={() => void doImport()} disabled={busy || !mappingValid}>
            {busy ? 'Importing…' : `Import ${preview.total_rows} row(s)`}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
