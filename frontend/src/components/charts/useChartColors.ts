import { useTheme } from '@mui/material';

export interface ChartColors {
  categorical: string[];
  axis: string;
  grid: string;
  text: string;
  tooltipBg: string;
  tooltipBorder: string;
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
}

/** Theme-aware colors so charts adapt to light / dark mode. */
export function useChartColors(): ChartColors {
  const theme = useTheme();
  const p = theme.palette;
  return {
    categorical: [
      p.primary.main,
      p.secondary.main,
      p.success.main,
      p.warning.main,
      p.info.main,
      p.error.main,
      '#A78BFA',
      '#F472B6',
      '#34D399',
      '#FBBF24',
    ],
    axis: p.text.secondary,
    grid: p.divider,
    text: p.text.primary,
    tooltipBg: p.background.paper,
    tooltipBorder: p.divider,
    primary: p.primary.main,
    secondary: p.secondary.main,
    success: p.success.main,
    warning: p.warning.main,
    error: p.error.main,
    info: p.info.main,
  };
}
