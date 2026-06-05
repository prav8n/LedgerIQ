import { useMemo } from 'react';
import type { ReactNode } from 'react';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { getTheme } from '@/theme/theme';
import { useThemeStore } from '@/store/themeStore';

interface Props {
  children: ReactNode;
}

export function ThemeModeProvider({ children }: Props) {
  const mode = useThemeStore((s) => s.mode);
  const theme = useMemo(() => getTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
