export type InsightType = 'positive' | 'warning' | 'tip' | 'info';

export interface Insight {
  id: string;
  type: InsightType;
  title: string;
  description: string;
  category: string;
  metric: string | null;
}

export interface InsightsResponse {
  period: string;
  insights: Insight[];
}

export type InsightPeriod = 'weekly' | 'monthly' | 'yearly';
