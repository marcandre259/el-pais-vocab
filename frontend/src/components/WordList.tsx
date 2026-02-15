import { WordCard } from './WordCard';
import { Button } from './ui';
import type { VocabularyWord } from '../api/types';
import styles from './WordList.module.css';

interface WordListProps {
  words: VocabularyWord[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

export function WordList({
  words,
  page,
  totalPages,
  onPageChange,
  isLoading,
}: WordListProps) {
  if (isLoading) {
    return (
      <div className={styles.loading}>
        <span className={styles.spinner} />
        <p>Loading vocabulary...</p>
      </div>
    );
  }

  if (words.length === 0) {
    return (
      <div className={styles.empty}>
        <p className={styles.emptyText}>No vocabulary words yet</p>
        <p className={styles.emptyHint}>
          Extract words from an article or generate a themed vocabulary list to
          get started.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.grid}>
        {words.map((word) => (
          <WordCard key={word.id} word={word} />
        ))}
      </div>

      {totalPages > 1 && (
        <nav className={styles.pagination} aria-label="Pagination">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            Previous
          </Button>

          <span className={styles.pageInfo}>
            Page {page} of {totalPages}
          </span>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </nav>
      )}
    </div>
  );
}
