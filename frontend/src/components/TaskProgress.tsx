import type { TaskStatus } from '../api/types';
import styles from './TaskProgress.module.css';

interface TaskProgressProps {
  task: TaskStatus;
  onDismiss?: () => void;
  onSyncRequest?: () => void;
}

const TASK_LABELS: Record<string, string> = {
  article_extract: 'Extracting vocabulary',
  theme_create: 'Generating vocabulary',
  audio_generate: 'Generating audio',
  anki_sync: 'Syncing to Anki',
};

export function TaskProgress({ task, onDismiss, onSyncRequest }: TaskProgressProps) {
  const isRunning = task.status === 'pending' || task.status === 'in_progress';
  const isComplete = task.status === 'completed';
  const isFailed = task.status === 'failed';

  const label = TASK_LABELS[task.type] || 'Processing';

  const showSyncButton = isComplete &&
    (task.type === 'article_extract' || task.type === 'theme_create') &&
    onSyncRequest;

  return (
    <div
      className={`${styles.container} ${isComplete ? styles.success : ''} ${isFailed ? styles.error : ''}`}
    >
      <div className={styles.content}>
        {isRunning && <span className={styles.spinner} aria-hidden="true" />}
        {isComplete && <span className={styles.checkmark} aria-hidden="true" />}
        {isFailed && <span className={styles.errorIcon} aria-hidden="true" />}

        <div className={styles.info}>
          <p className={styles.label}>
            {isRunning && `${label}...`}
            {isComplete && 'Complete!'}
            {isFailed && 'Failed'}
          </p>
          {task.progress && isRunning && (
            <p className={styles.progress}>{task.progress}</p>
          )}
          {isComplete && task.result !== undefined && task.result !== null && (
            <p className={styles.result}>{formatResult(task)}</p>
          )}
          {isFailed && task.error && (
            <p className={styles.errorMessage}>{task.error}</p>
          )}
          {showSyncButton && (
            <button className={styles.syncButton} onClick={onSyncRequest}>
              Sync to Anki
            </button>
          )}
        </div>
      </div>

      {(isComplete || isFailed) && onDismiss && (
        <button
          className={styles.dismiss}
          onClick={onDismiss}
          aria-label="Dismiss"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M4 4L12 12M4 12L12 4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      )}
    </div>
  );
}

function formatResult(task: TaskStatus): string {
  const result = task.result as Record<string, unknown> | undefined;
  if (!result) return '';

  if (task.type === 'article_extract' || task.type === 'theme_create') {
    const newWords = result.new_words as number;
    const updatedWords = result.updated_words as number;
    const parts: string[] = [];
    if (newWords > 0) parts.push(`${newWords} new word${newWords !== 1 ? 's' : ''}`);
    if (updatedWords > 0) parts.push(`${updatedWords} updated`);
    return parts.join(', ') || 'No new words';
  }

  if (task.type === 'audio_generate') {
    const generated = result.generated as number;
    return `${generated} audio file${generated !== 1 ? 's' : ''} generated`;
  }

  if (task.type === 'anki_sync') {
    const added = result.total_added as number;
    const skipped = result.total_skipped as number;
    return `${added} added, ${skipped} already synced`;
  }

  return '';
}
