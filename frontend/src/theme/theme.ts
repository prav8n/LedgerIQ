import { alpha, createTheme } from '@mui/material/styles';
import type { ThemeMode } from '@/store/themeStore';

// Brand palette — modern fintech (CRED / Fi inspired).
const BRAND = {
  primary: '#6C5CE7',
  primaryDark: '#5848d6',
  secondary: '#00D1B2',
  success: '#22C55E',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
};

export function getTheme(mode: ThemeMode) {
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode,
      primary: { main: BRAND.primary, dark: BRAND.primaryDark, contrastText: '#fff' },
      secondary: { main: BRAND.secondary },
      success: { main: BRAND.success },
      warning: { main: BRAND.warning },
      error: { main: BRAND.error },
      info: { main: BRAND.info },
      background: isDark
        ? { default: '#0B0B0F', paper: '#15151D' }
        : { default: '#F6F7FB', paper: '#FFFFFF' },
      text: isDark
        ? { primary: '#F3F4F6', secondary: '#9CA3AF' }
        : { primary: '#111827', secondary: '#6B7280' },
      divider: isDark ? alpha('#FFFFFF', 0.08) : alpha('#000000', 0.08),
    },
    shape: { borderRadius: 14 },
    typography: {
      fontFamily:
        '"Inter", "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
      h1: { fontWeight: 700, fontSize: '2.25rem' },
      h2: { fontWeight: 700, fontSize: '1.875rem' },
      h3: { fontWeight: 700, fontSize: '1.5rem' },
      h4: { fontWeight: 700, fontSize: '1.25rem' },
      h5: { fontWeight: 600, fontSize: '1.125rem' },
      h6: { fontWeight: 600, fontSize: '1rem' },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: { scrollbarWidth: 'thin' },
        },
      },
      MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: { root: { borderRadius: 10, paddingInline: 18 } },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            border: `1px solid ${isDark ? alpha('#FFFFFF', 0.06) : alpha('#000000', 0.06)}`,
          },
        },
      },
      MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
      MuiTextField: { defaultProps: { variant: 'outlined', size: 'medium' } },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            backdropFilter: 'blur(8px)',
          },
        },
      },
    },
  });
}
