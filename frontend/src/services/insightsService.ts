import { api } from '@/services/api';
import type { InsightPeriod, InsightsResponse } from '@/types/insight';

export const insightsService = {
  get: async (period: InsightPeriod): Promise<InsightsResponse> =>
    (await api.get<InsightsResponse>('/insights', { params: { period } })).data,
};
