import { api } from '@/services/api';
import type { AnalyticsResponse } from '@/types/analytics';
import type { PeriodQuery } from '@/utils/period';

export const analyticsService = {
  async get(query: PeriodQuery): Promise<AnalyticsResponse> {
    const { data } = await api.get<AnalyticsResponse>('/analytics', { params: query });
    return data;
  },
};
