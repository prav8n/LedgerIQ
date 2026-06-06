import { Controller } from 'react-hook-form';
import type { Control, FieldValues, Path } from 'react-hook-form';
import { FormControlLabel, Stack, Switch } from '@mui/material';
import { InfoTip } from '@/components/InfoTip';

interface Props<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
  /** Optional explanation shown as a hoverable ⓘ icon next to the label. */
  info?: string;
}

/** Fully-controlled MUI Switch bound to react-hook-form. */
export function RHFSwitch<T extends FieldValues>({ control, name, label, info }: Props<T>) {
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
          label={
            info ? (
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <span>{label}</span>
                <InfoTip text={info} />
              </Stack>
            ) : (
              label
            )
          }
        />
      )}
    />
  );
}
