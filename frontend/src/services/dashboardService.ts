import { api } from '@/services/api';
import type { DashboardResponse } from '@/types/dashboard';

export const dashboardService = {
  async get(months = 6, year?: number, month?: number): Promise<DashboardResponse> {
    const params: Record<string, number> = { months };
    if (year !== undefined && month !== undefined) {
      params.year = year;
      params.month = month;
    }
    const { data } = await api.get<DashboardResponse>('/dashboard', { params });
    return data;
  },
};
