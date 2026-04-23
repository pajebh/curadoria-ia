'use client';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
import type { UseFormRegister } from 'react-hook-form';
import styles from './ContextoForm.module.css';

interface ContextoFormProps {
  // Accepts the parent form's register — field paths are validated at the call site
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  register: UseFormRegister<any>;
}

export function ContextoForm({ register }: ContextoFormProps) {
  return (
    <div className={styles.grid}>
      {/* Nível */}
      <div className={styles.field}>
        <label htmlFor="ctx-nivel" className={styles.label}>
          O quanto você já sabe sobre o tema?
        </label>
        <select
          id="ctx-nivel"
          className={styles.select}
          {...register('contexto.nivel')}
        >
          <option value="">Não informar</option>
          <option value="zero">Iniciante absoluto — nunca explorei</option>
          <option value="basico">Básico — sei o essencial</option>
          <option value="intermediario">Intermediário — tenho uma base sólida</option>
          <option value="avancado">Avançado — conheço bem o tema</option>
        </select>
      </div>

      {/* Orçamento */}
      <div className={styles.field}>
        <label htmlFor="ctx-orcamento" className={styles.label}>
          Prefere recursos gratuitos ou investe?
        </label>
        <select
          id="ctx-orcamento"
          className={styles.select}
          {...register('contexto.orcamento')}
        >
          <option value="">Não informar</option>
          <option value="gratuito">Apenas recursos gratuitos</option>
          <option value="aberto_a_investimentos">Aberto a cursos e experiências pagas</option>
        </select>
      </div>

      {/* Idioma */}
      <div className={styles.field}>
        <label htmlFor="ctx-idioma" className={styles.label}>
          Em quais idiomas consome conteúdo?
        </label>
        <select
          id="ctx-idioma"
          className={styles.select}
          {...register('contexto.idioma')}
        >
          <option value="">Não informar</option>
          <option value="apenas_portugues">Apenas Português</option>
          <option value="aceita_ingles">Aceita Inglês</option>
          <option value="aceita_outros">Aceita outros idiomas</option>
        </select>
      </div>

      {/* Rotina */}
      <div className={styles.field}>
        <label htmlFor="ctx-rotina" className={styles.label}>
          Como costuma aprender no dia a dia?
        </label>
        <select
          id="ctx-rotina"
          className={styles.select}
          {...register('contexto.rotina')}
        >
          <option value="">Não informar</option>
          <option value="prefere_ler">Prefere ler — artigos, livros</option>
          <option value="prefere_ouvir">Prefere ouvir — podcasts, no trânsito</option>
          <option value="prefere_assistir">Prefere assistir — vídeos, documentários</option>
        </select>
      </div>

      {/* Localização — full width, não persiste */}
      <div className={`${styles.field} ${styles.fullWidth}`}>
        <label htmlFor="ctx-localizacao" className={styles.label}>
          Onde você está?
          <span className={styles.labelHint}> — para sugerir experiências locais</span>
        </label>
        <input
          id="ctx-localizacao"
          type="text"
          placeholder="Ex: São Paulo, SP"
          maxLength={100}
          className={styles.input}
          autoComplete="off"
          {...register('contexto.localizacao')}
        />
      </div>

      {/* Motivação — full width */}
      <div className={`${styles.field} ${styles.fullWidth}`}>
        <label htmlFor="ctx-motivacao" className={styles.label}>
          Qual é sua principal motivação?
        </label>
        <select
          id="ctx-motivacao"
          className={styles.select}
          {...register('contexto.motivacao')}
        >
          <option value="">Não informar</option>
          <option value="carreira">Carreira — mudar de área ou crescer profissionalmente</option>
          <option value="hobby">Hobby — explorar por prazer</option>
          <option value="curiosidade">Curiosidade Intelectual — entender mais profundamente</option>
          <option value="repertorio_social">Repertório Social — ser mais interessante nas conversas</option>
        </select>
      </div>
    </div>
  );
}
