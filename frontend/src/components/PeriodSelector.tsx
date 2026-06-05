import { IconButton, MenuItem, Stack, TextField, Typography } from '@mui/material';
import ChevronLeftRoundedIcon from '@mui/icons-material/ChevronLeftRounded';
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded';
import {
  GRANULARITY_OPTIONS,
  type Granularity,
  type PeriodState,
  periodLabel,
  shiftPeriod,
} from '@/utils/period';

interface Props {
  value: PeriodState;
  onChange: (next: PeriodState) => void;
  /** Restrict the granularity choices (e.g. `['monthly']` for month-only). */
  granularities?: Granularity[];
  size?: 'small' | 'medium';
}

/** Granularity dropdown + previous/next stepper with the current period label. */
export function PeriodSelector({ value, onChange, granularities, size = 'small' }: Props) {
  const options = GRANULARITY_OPTIONS.filter(
    (o) => !granularities || granularities.includes(o.value),
  );

  return (
    <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
      {options.length > 1 && (
        <TextField
          select
          size={size}
          value={value.granularity}
          onChange={(e) =>
            onChange({ ...value, granularity: e.target.value as Granularity })
          }
          sx={{ minWidth: 150 }}
        >
          {options.map((o) => (
            <MenuItem key={o.value} value={o.value}>
              {o.label}
            </MenuItem>
          ))}
        </TextField>
      )}
      <Stack direction="row" spacing={0.5} alignItems="center">
        <IconButton
          size="small"
          aria-label="Previous period"
          onClick={() => onChange(shiftPeriod(value, -1))}
        >
          <ChevronLeftRoundedIcon />
        </IconButton>
        <Typography
          variant="subtitle2"
          sx={{ minWidth: 170, textAlign: 'center', fontWeight: 700 }}
        >
          {periodLabel(value)}
        </Typography>
        <IconButton
          size="small"
          aria-label="Next period"
          onClick={() => onChange(shiftPeriod(value, 1))}
        >
          <ChevronRightRoundedIcon />
        </IconButton>
      </Stack>
    </Stack>
  );
}
