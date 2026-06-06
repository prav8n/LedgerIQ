import { Controller } from 'react-hook-form';
import type { Control, FieldValues, Path } from 'react-hook-form';
import { InputAdornment, TextField } from '@mui/material';
import { InfoTip } from '@/components/InfoTip';

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
  /** Optional explanation shown as a hoverable ⓘ icon in the field. */
  info?: string;
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
  info,
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
          // Stop mouse-wheel scrolling from silently changing a focused number
          // field (e.g. 249 -> 248.97). Blur removes focus so the wheel is ignored.
          onWheel={
            type === 'number'
              ? (e) => (e.target as HTMLElement).blur()
              : undefined
          }
          inputProps={
            type === 'number' ? { step: step ?? '0.01', min: min ?? '0', max } : undefined
          }
          InputProps={
            info
              ? {
                  endAdornment: (
                    <InputAdornment position="end">
                      <InfoTip text={info} />
                    </InputAdornment>
                  ),
                }
              : undefined
          }
          error={Boolean(fieldState.error)}
          helperText={fieldState.error?.message ?? helperText}
        />
      )}
    />
  );
}
