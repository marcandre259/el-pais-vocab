import type { FormEvent } from 'react';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { translateManualWords } from '../api/client';
import { Button, Select, Card, CardHeader } from './ui';
import { ThemeSelector } from './ThemeSelector';
import { LANGUAGE_OPTIONS } from '../constants';
import type { ManualEntryRequest, Theme } from '../api/types';
import styles from './ManualEntryForm.module.css';

interface ManualEntryFormProps {
  onTaskStart: (taskId: string) => void;
  disabled?: boolean;
}

export function ManualEntryForm({ onTaskStart, disabled }: ManualEntryFormProps) {
  const [theme, setTheme] = useState('');
  const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);
  const [wordsText, setWordsText] = useState('');
  const [sourceLang, setSourceLang] = useState('Dutch');
  const [targetLang, setTargetLang] = useState('English');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: translateManualWords,
    onSuccess: (data) => {
      onTaskStart(data.task_id);
      setWordsText('');
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['themes'] });
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'Translation failed');
    },
  });

  const handleThemeSelect = (t: Theme | null) => {
    setSelectedTheme(t);
    if (t) {
      setSourceLang(t.source_lang);
      setTargetLang(t.target_lang);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!theme.trim()) {
      setError('Please select or enter a theme');
      return;
    }

    const words = wordsText
      .split(/[,\n]+/)
      .map((w) => w.trim())
      .filter(Boolean);

    if (words.length === 0) {
      setError('Please enter at least one word');
      return;
    }

    const request: ManualEntryRequest = {
      words,
      source_lang: sourceLang,
      target_lang: targetLang,
      theme: theme.trim(),
    };

    mutation.mutate(request);
  };

  const isLoading = mutation.isPending || disabled;

  return (
    <Card variant="elevated" padding="lg">
      <CardHeader
        title="Add Words Manually"
        subtitle="Translate specific words and add them to a theme"
      />

      <form onSubmit={handleSubmit} className={styles.form}>
        <ThemeSelector
          value={theme}
          onChange={setTheme}
          onThemeSelect={handleThemeSelect}
          selectedTheme={selectedTheme}
          disabled={isLoading}
        />

        <div>
          <p className={styles.textareaLabel}>Words</p>
          <textarea
            className={styles.textarea}
            placeholder="Enter words separated by commas or new lines"
            value={wordsText}
            onChange={(e) => setWordsText(e.target.value)}
            disabled={isLoading}
            rows={3}
          />
        </div>

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
          </div>
        )}

        {error && <p className={styles.error}>{error}</p>}

        <Button type="submit" loading={mutation.isPending} disabled={isLoading}>
          Translate & Add
        </Button>
      </form>
    </Card>
  );
}
