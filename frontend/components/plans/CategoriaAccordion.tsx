'use client';

import { useState } from 'react';
import * as Accordion from '@radix-ui/react-accordion';
import * as Checkbox from '@radix-ui/react-checkbox';
import { CaretDown, Check } from '@phosphor-icons/react';
import { api } from '@/lib/api/client';
import styles from './CategoriaAccordion.module.css';

const CATEGORIA_LABELS: Record<string, string> = {
  formal:       'Aulas & Cursos',
  visual:       'Olhares em Movimento',
  leitura:      'Leitura',
  audio:        'Escuta',
  experiencias: 'Experiência',
  referencias:  'Vozes',
};

export interface PlanItem {
  id: string;
  nome: string;
  link: string;
  justificativa: string;
  concluido: boolean;
  ordem: number;
  is_wildcard: boolean;
}

export interface PlanCategory {
  id: string;
  nome: string;
  ordem: number;
  itens: PlanItem[];
}

interface CategoriaAccordionProps {
  planId: string;
  categorias: PlanCategory[];
}

export function CategoriaAccordion({ planId, categorias }: CategoriaAccordionProps) {
  const [concluidos, setConcluidos] = useState<Record<string, boolean>>(
    () => Object.fromEntries(
      categorias.flatMap(c => c.itens.map(i => [i.id, i.concluido]))
    )
  );

  async function toggleItem(itemId: string, checked: boolean) {
    setConcluidos(prev => ({ ...prev, [itemId]: checked }));
    try {
      await api.patch(`/planos/${planId}/itens/${itemId}`, { concluido: checked });
    } catch {
      setConcluidos(prev => ({ ...prev, [itemId]: !checked }));
    }
  }

  const sorted = [...categorias].sort((a, b) => a.ordem - b.ordem);

  return (
    <Accordion.Root
      type="multiple"
      defaultValue={sorted.map(c => c.id)}
      className={styles.root}
    >
      {sorted.map(categoria => (
        <Accordion.Item
          key={categoria.id}
          value={categoria.id}
          className={`${styles.item} ${styles[categoria.nome]}`}
        >
          <Accordion.Header className={styles.header}>
            <Accordion.Trigger className={styles.trigger}>
              <span className={styles.categoryName}>
                {CATEGORIA_LABELS[categoria.nome] ?? categoria.nome}
              </span>
              <span className={styles.count}>
                {categoria.itens.filter(i => concluidos[i.id]).length}/{categoria.itens.length}
              </span>
              <CaretDown className={styles.chevron} weight="bold" aria-hidden />
            </Accordion.Trigger>
          </Accordion.Header>

          <Accordion.Content className={styles.content}>
            <ul className={styles.itemList}>
              {[...categoria.itens]
                .sort((a, b) => a.ordem - b.ordem)
                .map(item => (
                  <li key={item.id} className={styles.itemRow}>
                    <Checkbox.Root
                      className={styles.checkbox}
                      checked={concluidos[item.id] ?? false}
                      onCheckedChange={v => toggleItem(item.id, v === true)}
                      aria-label={`Marcar "${item.nome}" como concluído`}
                    >
                      <Checkbox.Indicator>
                        <Check weight="bold" size={12} />
                      </Checkbox.Indicator>
                    </Checkbox.Root>

                    <div className={styles.itemContent}>
                      <a
                        href={item.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`${styles.itemNome} ${concluidos[item.id] ? styles.concluido : ''}`}
                      >
                        {item.nome}
                        {item.is_wildcard && (
                          <span
                            className={styles.wildcardBadge}
                            aria-label="Fator de Descoberta"
                          >
                            🎲 Descoberta
                          </span>
                        )}
                      </a>
                      <p className={styles.justificativa}>{item.justificativa}</p>
                    </div>
                  </li>
                ))}
            </ul>
          </Accordion.Content>
        </Accordion.Item>
      ))}
    </Accordion.Root>
  );
}
