import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getVocabulary, getVocabularyStats, getThemes } from '../api/client';
import { Select } from '../components/ui';
import { WordList } from '../components/WordList';
import styles from './Browse.module.css';

export function Browse() {
  const [page, setPage] = useState(1);
  const [selectedTheme, setSelectedTheme] = useState<string>('');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', selectedTheme || undefined],
    queryFn: () => getVocabularyStats(selectedTheme || undefined),
  });

  const { data: vocabulary, isLoading: vocabLoading } = useQuery({
    queryKey: ['vocabulary', page, selectedTheme || undefined],
    queryFn: () => getVocabulary(page, 30, selectedTheme || undefined),
  });

  const { data: themes } = useQuery({
    queryKey: ['themes'],
    queryFn: getThemes,
  });

  const themeOptions = [
    { value: '', label: 'All themes' },
    { value: 'el_pais', label: 'El Pais Articles' },
    ...(themes?.map((t) => ({
      value: t.table_name,
      label: t.theme_description,
    })) || []),
  ];

  const handleThemeChange = (theme: string) => {
    setSelectedTheme(theme);
    setPage(1); // Reset to first page when filter changes
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Vocabulary</h1>
        <p className={styles.subtitle}>Browse and manage your saved words</p>
      </header>

      <div className={styles.controls}>
        <div className={styles.stats}>
          {statsLoading ? (
            <p className={styles.statLoading}>Loading stats...</p>
          ) : stats ? (
            <>
              <StatCard
                label="Total words"
                value={stats.total_words}
                highlight
              />
              {Object.entries(stats.by_pos)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 4)
                .map(([pos, count]) => (
                  <StatCard key={pos} label={pos} value={count} />
                ))}
            </>
          ) : null}
        </div>

        <div className={styles.filter}>
          <Select
            label="Filter by theme"
            options={themeOptions}
            value={selectedTheme}
            onChange={(e) => handleThemeChange(e.target.value)}
          />
        </div>
      </div>

      <WordList
        words={vocabulary?.items || []}
        page={page}
        totalPages={vocabulary?.total_pages || 1}
        onPageChange={setPage}
        isLoading={vocabLoading}
      />
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  highlight?: boolean;
}

function StatCard({ label, value, highlight }: StatCardProps) {
  return (
    <div className={`${styles.statCard} ${highlight ? styles.highlight : ''}`}>
      <span className={styles.statValue}>{value}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}
