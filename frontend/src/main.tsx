import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ThemeModeProvider } from '@/theme/ThemeModeProvider';
import { ToastViewport } from '@/components/ToastViewport';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { queryClient } from '@/config/queryClient';
import { App } from '@/App';

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element #root not found');
}

createRoot(container).render(
  <StrictMode>
    <ThemeModeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ErrorBoundary>
            <App />
          </ErrorBoundary>
          <ToastViewport />
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeModeProvider>
  </StrictMode>,
);
