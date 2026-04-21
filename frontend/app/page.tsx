import type { Metadata } from 'next';
import styles from './page.module.css';

export const metadata: Metadata = {
  title: 'CuradorIA',
};

export default function HomePage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.logo}>CuradorIA</h1>
      </header>

      <section className={styles.hero} aria-labelledby="headline">
        <h2 id="headline" className={styles.headline}>
          O que você quer aprender?
        </h2>
        {/* TODO: PlanoForm component */}
        <p className={styles.placeholder}>
          Formulário de criação de plano — em desenvolvimento.
        </p>
      </section>

      <section aria-labelledby="planos-recentes-titulo">
        <h2 id="planos-recentes-titulo" className={styles.sectionTitle}>
          Seus planos recentes
        </h2>
        {/* TODO: lista de planos históricos */}
        <p className={styles.muted}>Nenhum plano ainda. Crie o primeiro acima!</p>
      </section>
    </div>
  );
}
