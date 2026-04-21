import type { HTMLAttributes, ReactNode } from 'react';
import styles from './Card.module.css';

type Category = 'formal' | 'visual' | 'leitura' | 'audio' | 'experiencias' | 'referencias';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  category?: Category;
  children: ReactNode;
}

export function Card({ category, children, className, ...props }: CardProps) {
  return (
    <div
      className={[styles.card, category ? styles[category] : '', className].filter(Boolean).join(' ')}
      {...props}
    >
      {children}
    </div>
  );
}
