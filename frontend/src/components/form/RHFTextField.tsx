import { Controller } from 'react-hook-form';
import type { Control, FieldValues, Path } from 'react-hook-form';
import { TextField } from '@mui/material';

interface Props<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
  type?: 'text' | 'number' | 'date';
  required?: boolean;
  step?: string;
  min?: string;
  max?: string;
  multiline?: boolean;
  helperText?: string;
  autoFocus?: boolean;
}

/** Fully-controlled MUI TextField bound to react-hook-form. */
export function RHFTextField<T extends FieldValues>({
  control,
  name,
  label,
  type = 'text',
  required = false,
  step,
  min,
  max,
  multiline,
  helperText,
  autoFocus,
}: Props<T>) {
  return (
    <Controller
      control={control}
      name={name}
      rules={{ required: required ? `${label} is required` : false }}
      render={({ field, fieldState }) => (
        <TextField
          {...field}
          value={field.value ?? ''}
          label={label}
          type={type}
          fullWidth
          autoFocus={autoFocus}
          multiline={multiline}
          minRows={multiline ? 2 : undefined}
          InputLabelProps={type === 'date' ? { shrink: true } : undefined}
          inputProps={
            type === 'number' ? { step: step ?? '0.01', min: min ?? '0', max } : undefined
          }
          error={Boolean(fieldState.error)}
          helperText={fieldState.error?.message ?? helperText}
        />
      )}
    />
  );
}
