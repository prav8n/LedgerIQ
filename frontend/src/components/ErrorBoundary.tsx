import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

/** Catches render-time errors in the subtree and shows a recoverable fallback. */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    // Replace with a real logger / Sentry in production.
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, message: '' });
  };

  override render(): ReactNode {
    if (!this.state.hasError) return this.props.children;
    if (this.props.fallback) return this.props.fallback;

    return (
      <Box sx={{ display: 'grid', placeItems: 'center', minHeight: '60vh', p: 3 }}>
        <Stack spacing={2} alignItems="center" textAlign="center">
          <ErrorOutlineRoundedIcon color="error" sx={{ fontSize: 56 }} />
          <Typography variant="h5">Something went wrong</Typography>
          <Typography variant="body2" color="text.secondary" maxWidth={460}>
            {this.state.message || 'An unexpected error occurred while rendering this page.'}
          </Typography>
          <Button variant="contained" onClick={this.handleReset}>
            Try again
          </Button>
        </Stack>
      </Box>
    );
  }
}
