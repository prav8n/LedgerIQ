import { useQuery } from '@tanstack/react-query';
import { insightsService } from '@/services/insightsService';
import type { InsightPeriod, InsightsResponse } from '@/types/insight';

export function useInsights(period: InsightPeriod = 'monthly') {
  return useQuery<InsightsResponse>({
    queryKey: ['insights', period],
    queryFn: () => insightsService.get(period),
  });
}
