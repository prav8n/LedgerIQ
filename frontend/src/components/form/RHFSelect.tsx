import { Controller } from 'react-hook-form';
import type { Control, FieldValues, Path } from 'react-hook-form';
import { MenuItem, TextField } from '@mui/material';
import type { Option } from '@/constants/enums';

interface Props<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
  options: Option[];
  /** When set, prepends an empty option with this label (value ''). */
  emptyLabel?: string;
}

/** Fully-controlled MUI select bound to react-hook-form. */
export function RHFSelect<T extends FieldValues>({
  control,
  name,
  label,
  options,
  emptyLabel,
}: Props<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => (
        <TextField select {...field} value={field.value ?? ''} label={label} fullWidth>
          {emptyLabel !== undefined && <MenuItem value="">{emptyLabel}</MenuItem>}
          {options.map((o) => (
            <MenuItem key={o.value} value={o.value}>
              {o.label}
            </MenuItem>
          ))}
        </TextField>
      )}
    />
  );
}
