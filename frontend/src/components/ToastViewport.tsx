import { Alert, Snackbar } from '@mui/material';
import { useToastStore } from '@/store/toastStore';

/**
 * Renders stacked toast snackbars driven by the toast store. Mount once near
 * the app root. Toasts auto-dismiss and stack from the bottom-right.
 */
export function ToastViewport() {
  const toasts = useToastStore((s) => s.toasts);
  const remove = useToastStore((s) => s.remove);

  return (
    <>
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open
          autoHideDuration={4000}
          onClose={() => remove(toast.id)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{ mb: `${index * 64}px` }}
        >
          <Alert
            severity={toast.severity}
            variant="filled"
            onClose={() => remove(toast.id)}
            sx={{ width: '100%', boxShadow: 6 }}
          >
            {toast.message}
          </Alert>
        </Snackbar>
      ))}
    </>
  );
}
