import { api } from '@/services/api';
import type { ImportMapping, ImportPreview, ImportResult } from '@/types/import';

const multipart = { headers: { 'Content-Type': 'multipart/form-data' } };

export const importService = {
  preview: async (file: File): Promise<ImportPreview> => {
    const form = new FormData();
    form.append('file', file);
    return (await api.post<ImportPreview>('/import/expenses/preview', form, multipart)).data;
  },
  commit: async (file: File, mapping: ImportMapping): Promise<ImportResult> => {
    const form = new FormData();
    form.append('file', file);
    form.append('mapping', JSON.stringify(mapping));
    return (await api.post<ImportResult>('/import/expenses', form, multipart)).data;
  },
};
