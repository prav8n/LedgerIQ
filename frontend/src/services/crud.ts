import { api } from '@/services/api';

export interface CrudService<TRead, TCreate, TUpdate> {
  list: (params?: Record<string, unknown>) => Promise<TRead[]>;
  get: (id: number) => Promise<TRead>;
  create: (body: TCreate) => Promise<TRead>;
  update: (id: number, body: TUpdate) => Promise<TRead>;
  remove: (id: number) => Promise<void>;
}

/** Build a standard CRUD service bound to a base path (list returns an array). */
export function makeCrudService<TRead, TCreate, TUpdate>(
  base: string,
): CrudService<TRead, TCreate, TUpdate> {
  return {
    list: async (params) => (await api.get<TRead[]>(base, { params })).data,
    get: async (id) => (await api.get<TRead>(`${base}/${id}`)).data,
    create: async (body) => (await api.post<TRead>(base, body)).data,
    update: async (id, body) => (await api.put<TRead>(`${base}/${id}`, body)).data,
    remove: async (id) => {
      await api.delete(`${base}/${id}`);
    },
  };
}
