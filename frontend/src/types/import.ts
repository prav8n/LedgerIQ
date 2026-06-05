export type ImportField =
  | 'transaction_date'
  | 'amount'
  | 'merchant'
  | 'description'
  | 'category'
  | 'payment_method';

export type ImportMapping = Record<ImportField, string | null>;

export interface ImportPreview {
  headers: string[];
  suggested_mapping: ImportMapping;
  sample_rows: Record<string, string>[];
  total_rows: number;
}

export interface ImportRowError {
  row: number;
  error: string;
}

export interface ImportResult {
  created: number;
  skipped: number;
  errors: ImportRowError[];
}
