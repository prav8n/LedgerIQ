import { Controller } from 'react-hook-form';
import type { Control, FieldValues, Path } from 'react-hook-form';
import { FormControlLabel, Switch } from '@mui/material';

interface Props<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
}

/** Fully-controlled MUI Switch bound to react-hook-form. */
export function RHFSwitch<T extends FieldValues>({ control, name, label }: Props<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => (
        <FormControlLabel
          control={
            <Switch
              checked={Boolean(field.value)}
              onChange={(e) => field.onChange(e.target.checked)}
              onBlur={field.onBlur}
            />
          }
          label={label}
        />
      )}
    />
  );
}
