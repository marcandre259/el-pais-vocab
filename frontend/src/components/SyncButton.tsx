import { useState, useEffect } from 'react';
import { checkAnkiStatus, syncToAnki } from '../api/client';
import styles from './SyncButton.module.css';

interface SyncButtonProps {
  onTaskStart: (taskId: string) => void;
  disabled?: boolean;
}

export function SyncButton({ onTaskStart, disabled }: SyncButtonProps) {
  const [warning, setWarning] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (warning) {
      const timer = setTimeout(() => setWarning(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [warning]);

  const handleClick = async () => {
    setWarning(null);
    setLoading(true);

    try {
      const status = await checkAnkiStatus();
      if (!status.connected) {
        setWarning(status.message || 'Anki is not running or AnkiConnect is not installed');
        setLoading(false);
        return;
      }

      const response = await syncToAnki({ include_main: true, include_themes: true });
      onTaskStart(response.task_id);
    } catch {
      setWarning('Failed to connect to Anki');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button
        className={styles.syncButton}
        onClick={handleClick}
        disabled={disabled || loading}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M1.5 8a6.5 6.5 0 0 1 11.25-4.4M14.5 8a6.5 6.5 0 0 1-11.25 4.4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <path
            d="M12.75 1v2.6h-2.6M3.25 15v-2.6h2.6"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {loading ? 'Checking...' : 'Sync to Anki'}
      </button>
      {warning && <p className={styles.warning}>{warning}</p>}
    </div>
  );
}
