import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { CrudService } from '@/services/crud';

/** Build list/create/update/remove hooks for a CRUD service under one query key. */
export function createCrudHooks<TRead, TCreate, TUpdate>(
  key: string,
  service: CrudService<TRead, TCreate, TUpdate>,
) {
  const listKey = [key] as const;

  function useList(params?: Record<string, unknown>) {
    return useQuery<TRead[]>({
      queryKey: params ? [key, params] : listKey,
      queryFn: () => service.list(params),
    });
  }

  function useCreate() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: (body: TCreate) => service.create(body),
      onSuccess: () => void qc.invalidateQueries({ queryKey: [key] }),
    });
  }

  function useUpdate() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: (vars: { id: number; body: TUpdate }) =>
        service.update(vars.id, vars.body),
      onSuccess: () => void qc.invalidateQueries({ queryKey: [key] }),
    });
  }

  function useRemove() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: (id: number) => service.remove(id),
      onSuccess: () => void qc.invalidateQueries({ queryKey: [key] }),
    });
  }

  return { key, listKey, useList, useCreate, useUpdate, useRemove };
}
