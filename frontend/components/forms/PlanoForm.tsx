'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { SlidersHorizontal, CaretDown } from '@phosphor-icons/react';
import { api } from '@/lib/api/client';
import { usePerfilSessao } from '@/lib/hooks/usePerfilSessao';
import { ContextoForm } from './ContextoForm';
import { Button } from '@/components/ui/Button';
import type { ContextoUsuario } from '@/types/perfil';
import styles from './PlanoForm.module.css';

const schema = z.object({
  tema: z.string().min(3, 'Mínimo 3 caracteres').max(200, 'Máximo 200 caracteres'),
  tempo_valor: z.coerce.number().int().min(1).max(24),
  tempo_unidade: z.enum(['dias', 'semanas', 'meses']),
  contexto: z
    .object({
      nivel: z.string(),
      orcamento: z.string(),
      idioma: z.string(),
      rotina: z.string(),
      localizacao: z.string().max(100, 'Máximo 100 caracteres'),
      motivacao: z.string(),
    })
    .optional(),
});

type FormData = z.infer<typeof schema>;

interface PlanoCreateResponse {
  plano_id: string;
  stream_url: string;
}

function toContextoUsuario(raw: FormData['contexto']): ContextoUsuario | undefined {
  if (!raw) return undefined;

  const ctx: ContextoUsuario = {
    nivel: (raw.nivel || undefined) as ContextoUsuario['nivel'],
    orcamento: (raw.orcamento || undefined) as ContextoUsuario['orcamento'],
    idioma: (raw.idioma || undefined) as ContextoUsuario['idioma'],
    rotina: (raw.rotina || undefined) as ContextoUsuario['rotina'],
    localizacao: raw.localizacao?.trim() || undefined,
    motivacao: (raw.motivacao || undefined) as ContextoUsuario['motivacao'],
  };

  const hasValues = Object.values(ctx).some((v) => v !== undefined);
  return hasValues ? ctx : undefined;
}

export function PlanoForm() {
  const router = useRouter();
  const { perfil, isLoading: perfilLoading, upsert } = usePerfilSessao();
  const [detailsOpen, setDetailsOpen] = useState(false);
  const perfilAppliedRef = useRef(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      tempo_valor: 2,
      tempo_unidade: 'semanas',
      contexto: {
        nivel: '',
        orcamento: '',
        idioma: '',
        rotina: '',
        localizacao: '',
        motivacao: '',
      },
    },
  });

  // Pre-fill form from saved profile (once, on first load)
  useEffect(() => {
    if (!perfil || perfilAppliedRef.current) return;
    perfilAppliedRef.current = true;

    if (perfil.nivel) setValue('contexto.nivel', perfil.nivel);
    if (perfil.orcamento) setValue('contexto.orcamento', perfil.orcamento);
    if (perfil.idioma) setValue('contexto.idioma', perfil.idioma);
    if (perfil.rotina) setValue('contexto.rotina', perfil.rotina);
    if (perfil.motivacao) setValue('contexto.motivacao', perfil.motivacao);

    const hasAnyField = Object.values(perfil).some(
      (v) => v !== undefined && v !== null,
    );
    if (hasAnyField) setDetailsOpen(true);
  }, [perfil, setValue]);

  async function onSubmit(data: FormData) {
    try {
      const idempotencyKey = crypto.randomUUID();
      const contexto = toContextoUsuario(data.contexto);

      // Fire-and-forget: save profile fields (never saves localizacao)
      if (contexto) {
        const { localizacao: _loc, ...perfilData } = contexto;
        const hasPerfilFields = Object.values(perfilData).some((v) => v !== undefined);
        if (hasPerfilFields) upsert(perfilData);
      }

      const res = await api.post<PlanoCreateResponse>(
        '/planos',
        {
          tema: data.tema,
          tempo_valor: data.tempo_valor,
          tempo_unidade: data.tempo_unidade,
          ...(contexto ? { contexto } : {}),
        },
        idempotencyKey,
      );

      router.push(`/planos/${res.plano_id}`);
    } catch {
      setError('root', { message: 'Não foi possível criar o plano. Tente novamente.' });
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form} noValidate>
      <div className={styles.field}>
        <label htmlFor="tema" className={styles.label}>
          O que você quer explorar?
        </label>
        <input
          id="tema"
          type="text"
          placeholder="Ex: Jazz moderno, Estoicismo, Fotografia analógica…"
          className={styles.input}
          aria-describedby={errors.tema ? 'tema-error' : undefined}
          aria-invalid={!!errors.tema}
          {...register('tema')}
        />
        {errors.tema && (
          <p id="tema-error" className={styles.error} role="alert">
            {errors.tema.message}
          </p>
        )}
      </div>

      <div className={styles.tempoGroup}>
        <div className={styles.field}>
          <label htmlFor="tempo_valor" className={styles.label}>
            Quanto tempo você tem?
          </label>
          <input
            id="tempo_valor"
            type="number"
            min={1}
            max={24}
            className={`${styles.input} ${styles.inputNumber}`}
            aria-describedby={errors.tempo_valor ? 'tempo-error' : undefined}
            aria-invalid={!!errors.tempo_valor}
            {...register('tempo_valor')}
          />
        </div>

        <div className={`${styles.field} ${styles.fieldUnidade}`}>
          <label htmlFor="tempo_unidade" className={styles.label}>
            &nbsp;
          </label>
          <select
            id="tempo_unidade"
            className={`${styles.input} ${styles.select}`}
            {...register('tempo_unidade')}
          >
            <option value="dias">dias</option>
            <option value="semanas">semanas</option>
            <option value="meses">meses</option>
          </select>
        </div>
      </div>

      {/* Personalization section */}
      <details
        className={styles.personalizacao}
        open={detailsOpen}
        aria-busy={perfilLoading}
        data-testid="personalizacao"
        onToggle={(e) => setDetailsOpen((e.currentTarget as HTMLDetailsElement).open)}
      >
        <summary className={styles.personalizacaoTrigger} data-testid="personalizacao-trigger">
          <span className={styles.triggerLabel}>
            <SlidersHorizontal weight="duotone" size={18} aria-hidden="true" />
            Personalize seu plano
            <span className={styles.triggerBadge}>opcional</span>
          </span>
          <CaretDown
            weight="bold"
            size={16}
            className={styles.triggerCaret}
            aria-hidden="true"
          />
        </summary>

        <div className={styles.personalizacaoBody}>
          <p className={styles.personalizacaoHint}>
            Quanto mais contexto você der, mais preciso o plano. Todos os campos são opcionais.
          </p>
          <ContextoForm register={register} />
        </div>
      </details>

      {errors.root && (
        <p className={styles.error} role="alert">
          {errors.root.message}
        </p>
      )}

      <Button type="submit" loading={isSubmitting} size="lg">
        Criar plano de estudos
      </Button>
    </form>
  );
}
