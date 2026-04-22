import type { Metadata } from 'next';
import Link from 'next/link';
import { PlanoForm } from '@/components/forms/PlanoForm';
import styles from './page.module.css';

export const metadata: Metadata = {
  title: 'CuradorIA',
};

export default function HomePage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.logo}>CuradorIA</h1>
        <nav>
          <Link href="/historico" className={styles.navLink}>Histórico</Link>
        </nav>
      </header>

      <section className={styles.hero} aria-labelledby="headline">
        <h2 id="headline" className={styles.headline}>
          O que você quer aprender?
        </h2>
        <PlanoForm />
      </section>
    </div>
  );
}
