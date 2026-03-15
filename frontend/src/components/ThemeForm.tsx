import type { FormEvent } from 'react';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createTheme } from '../api/client';
import { Button, Select, Input, Card, CardHeader } from './ui';
import { ThemeSelector } from './ThemeSelector';
import { LANGUAGE_OPTIONS } from '../constants';
import type { ThemeCreateRequest, Theme } from '../api/types';
import styles from './ThemeForm.module.css';

interface ThemeFormProps {
  onTaskStart: (taskId: string) => void;
  disabled?: boolean;
}

export function ThemeForm({ onTaskStart, disabled }: ThemeFormProps) {
  const [themePrompt, setThemePrompt] = useState('');
  const [sourceLang, setSourceLang] = useState('Dutch');
  const [targetLang, setTargetLang] = useState('English');
  const [wordCount, setWordCount] = useState('20');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: createTheme,
    onSuccess: (data) => {
      onTaskStart(data.task_id);
      setThemePrompt('');
      setSelectedTheme(null);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['themes'] });
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'Generation failed');
    },
  });

  const handleThemeSelect = (theme: Theme | null) => {
    setSelectedTheme(theme);
    if (theme) {
      setSourceLang(theme.source_lang);
      setTargetLang(theme.target_lang);
    } else {
      setSourceLang('Dutch');
      setTargetLang('English');
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!themePrompt.trim()) {
      setError('Please enter a theme');
      return;
    }

    const request: ThemeCreateRequest = {
      theme_prompt: themePrompt.trim(),
      source_lang: sourceLang,
      target_lang: targetLang,
      word_count: parseInt(wordCount, 10) || 20,
    };

    mutation.mutate(request);
  };

  const isLoading = mutation.isPending || disabled;

  return (
    <Card variant="elevated" padding="lg">
      <CardHeader
        title="Generate Themed Vocabulary"
        subtitle="Create vocabulary lists for any topic and language pair"
      />

      <form onSubmit={handleSubmit} className={styles.form}>
        <ThemeSelector
          value={themePrompt}
          onChange={setThemePrompt}
          onThemeSelect={handleThemeSelect}
          selectedTheme={selectedTheme}
          disabled={isLoading}
        />

        {error && !themePrompt.trim() && <p className={styles.error}>{error}</p>}

        <button
          type="button"
          className={styles.advancedToggle}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? 'Hide' : 'Show'} options
          <svg
            className={`${styles.chevron} ${showAdvanced ? styles.open : ''}`}
            width="12"
            height="8"
            viewBox="0 0 12 8"
            fill="none"
          >
            <path
              d="M1 1.5L6 6.5L11 1.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        {showAdvanced && (
          <div className={styles.advanced}>
            <div className={styles.row}>
              <Select
                label="Source language"
                options={LANGUAGE_OPTIONS}
                value={sourceLang}
                onChange={(e) => setSourceLang(e.target.value)}
                disabled={isLoading}
              />
              <Select
                label="Target language"
                options={LANGUAGE_OPTIONS}
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <Input
              label="Word count"
              type="number"
              min="1"
              max="1000"
              value={wordCount}
              onChange={(e) => setWordCount(e.target.value)}
              disabled={isLoading}
            />
          </div>
        )}

        {error && themePrompt.trim() && <p className={styles.error}>{error}</p>}

        <Button type="submit" loading={mutation.isPending} disabled={isLoading}>
          {selectedTheme ? 'Add More Words' : 'Generate Vocabulary'}
        </Button>
      </form>
    </Card>
  );
}
