import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { analyticsService } from '@/services/analyticsService';
import type { AnalyticsResponse } from '@/types/analytics';
import { periodQuery, type PeriodState } from '@/utils/period';

export const analyticsKeys = {
  all: ['analytics'] as const,
  byPeriod: (p: PeriodState) =>
    ['analytics', p.granularity, p.year, p.month] as const,
};

export function useAnalytics(period: PeriodState) {
  return useQuery<AnalyticsResponse>({
    queryKey: analyticsKeys.byPeriod(period),
    queryFn: () => analyticsService.get(periodQuery(period)),
    // Keep the prior period's data visible while the next one loads.
    placeholderData: keepPreviousData,
  });
}
