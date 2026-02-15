import { useState } from 'react';
import { ArticleForm } from '../components/ArticleForm';
import { ThemeForm } from '../components/ThemeForm';
import { TaskProgress } from '../components/TaskProgress';
import { useTask, isTaskRunning } from '../hooks/useTask';
import { syncToAnki } from '../api/client';
import styles from './Home.module.css';

export function Home() {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const { data: taskStatus } = useTask(activeTaskId);

  const handleTaskStart = (taskId: string) => {
    setActiveTaskId(taskId);
  };

  const handleDismiss = () => {
    setActiveTaskId(null);
  };

  const handleSyncRequest = async () => {
    try {
      const response = await syncToAnki({ include_main: true, include_themes: true });
      setActiveTaskId(response.task_id);
    } catch (error) {
      console.error('Failed to start sync:', error);
    }
  };

  const isRunning = taskStatus && isTaskRunning(taskStatus);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Vocabulary Builder</h1>
        <p className={styles.subtitle}>
          Extract vocabulary from articles or generate themed word lists
        </p>
      </header>

      {taskStatus && (
        <div className={styles.taskProgress}>
          <TaskProgress
            task={taskStatus}
            onDismiss={handleDismiss}
            onSyncRequest={handleSyncRequest}
          />
        </div>
      )}

      <div className={styles.forms}>
        <ArticleForm onTaskStart={handleTaskStart} disabled={isRunning} />
        <ThemeForm onTaskStart={handleTaskStart} disabled={isRunning} />
      </div>
    </div>
  );
}
