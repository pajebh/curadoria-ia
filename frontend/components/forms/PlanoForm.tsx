'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { api } from '@/lib/api/client';
import { Button } from '@/components/ui/Button';
import styles from './PlanoForm.module.css';

const schema = z.object({
  tema: z.string().min(3, 'Mínimo 3 caracteres').max(200, 'Máximo 200 caracteres'),
  tempo_valor: z.coerce.number().int().min(1).max(24),
  tempo_unidade: z.enum(['dias', 'semanas', 'meses']),
});

type FormData = z.infer<typeof schema>;

interface PlanoCreateResponse {
  plano_id: string;
  stream_url: string;
}

export function PlanoForm() {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { tempo_valor: 2, tempo_unidade: 'semanas' },
  });

  async function onSubmit(data: FormData) {
    try {
      const idempotencyKey = crypto.randomUUID();
      const res = await api.post<PlanoCreateResponse>('/planos', data, idempotencyKey);
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
