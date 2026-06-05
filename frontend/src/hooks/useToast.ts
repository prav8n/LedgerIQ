import { useMemo } from 'react';
import { useToastStore } from '@/store/toastStore';

/**
 * Convenience wrapper around the toast store.
 * Usage: `const toast = useToast(); toast.success('Saved');`
 */
export function useToast() {
  const push = useToastStore((s) => s.push);
  return useMemo(
    () => ({
      success: (message: string) => push(message, 'success'),
      error: (message: string) => push(message, 'error'),
      info: (message: string) => push(message, 'info'),
      warning: (message: string) => push(message, 'warning'),
    }),
    [push],
  );
}
