'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { PerfilSessao } from '@/types/perfil';

const PERFIL_KEY = ['sessoes', 'perfil'] as const;

type PerfilInput = Omit<PerfilSessao, 'atualizado_em'>;

export function usePerfilSessao() {
  const queryClient = useQueryClient();

  const perfilQuery = useQuery<PerfilSessao | undefined>({
    queryKey: PERFIL_KEY,
    queryFn: () => api.get<PerfilSessao | undefined>('/sessoes/perfil'),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const upsertMutation = useMutation({
    mutationFn: (perfil: PerfilInput) =>
      api.put<PerfilSessao>('/sessoes/perfil', perfil),
    onSuccess: (data) => {
      queryClient.setQueryData(PERFIL_KEY, data);
    },
  });

  return {
    perfil: perfilQuery.data,
    isLoading: perfilQuery.isLoading,
    upsert: upsertMutation.mutate,
  };
}
