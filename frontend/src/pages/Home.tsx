import { ArticleForm } from '../components/ArticleForm';
import { ThemeForm } from '../components/ThemeForm';
import { ManualEntryForm } from '../components/ManualEntryForm';
import styles from './Home.module.css';

interface HomeProps {
  onTaskStart: (taskId: string) => void;
  disabled?: boolean;
}

export function Home({ onTaskStart, disabled }: HomeProps) {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Vocabulary Builder</h1>
        <p className={styles.subtitle}>
          Extract vocabulary from articles or generate themed word lists
        </p>
      </header>

      <div className={styles.forms}>
        <ArticleForm onTaskStart={onTaskStart} disabled={disabled} />
        <ThemeForm onTaskStart={onTaskStart} disabled={disabled} />
        <ManualEntryForm onTaskStart={onTaskStart} disabled={disabled} />
      </div>
    </div>
  );
}
