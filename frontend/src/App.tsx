import { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Home } from './pages/Home';
import { Browse } from './pages/Browse';
import { SyncButton } from './components/SyncButton';
import { TaskProgress } from './components/TaskProgress';
import { useTask, isTaskRunning } from './hooks/useTask';
import styles from './App.module.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

function AppContent() {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const { data: taskStatus } = useTask(activeTaskId);

  const handleTaskStart = (taskId: string) => {
    setActiveTaskId(taskId);
  };

  const handleDismiss = () => {
    setActiveTaskId(null);
  };

  const isRunning = taskStatus && isTaskRunning(taskStatus);

  return (
    <div className={styles.app}>
      <nav className={styles.nav}>
        <div className={styles.navContent}>
          <span className={styles.logo}>El Pais Vocab</span>
          <div className={styles.navRight}>
            <div className={styles.navLinks}>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `${styles.navLink} ${isActive ? styles.active : ''}`
                }
              >
                Capture
              </NavLink>
              <NavLink
                to="/browse"
                className={({ isActive }) =>
                  `${styles.navLink} ${isActive ? styles.active : ''}`
                }
              >
                Browse
              </NavLink>
            </div>
            <SyncButton onTaskStart={handleTaskStart} disabled={isRunning} />
          </div>
        </div>
      </nav>

      {taskStatus && (
        <div className={styles.taskBanner}>
          <TaskProgress task={taskStatus} onDismiss={handleDismiss} />
        </div>
      )}

      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<Home onTaskStart={handleTaskStart} disabled={isRunning} />} />
          <Route path="/browse" element={<Browse />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
