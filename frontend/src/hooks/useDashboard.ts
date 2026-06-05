import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/dashboardService';
import type { DashboardResponse } from '@/types/dashboard';

export const dashboardKeys = {
  all: ['dashboard'] as const,
  byMonths: (months: number) => ['dashboard', months] as const,
  byPeriod: (months: number, year?: number, month?: number) =>
    ['dashboard', months, year ?? null, month ?? null] as const,
};

export function useDashboard(months = 6, year?: number, month?: number) {
  return useQuery<DashboardResponse>({
    queryKey: dashboardKeys.byPeriod(months, year, month),
    queryFn: () => dashboardService.get(months, year, month),
    // Keep the previous month's data on screen while the next one loads.
    placeholderData: keepPreviousData,
  });
}
