import type { FormEvent } from 'react';
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createTheme, getThemes } from '../api/client';
import { Button, Input, Select, Card, CardHeader } from './ui';
import type { ThemeCreateRequest, Theme } from '../api/types';
import styles from './ThemeForm.module.css';

interface ThemeFormProps {
  onTaskStart: (taskId: string) => void;
  disabled?: boolean;
}

const LANGUAGE_OPTIONS = [
  { value: 'Spanish', label: 'Spanish' },
  { value: 'French', label: 'French' },
  { value: 'Italian', label: 'Italian' },
  { value: 'Portuguese', label: 'Portuguese' },
  { value: 'German', label: 'German' },
  { value: 'Dutch', label: 'Dutch' },
  { value: 'English', label: 'English' },
  { value: 'Japanese', label: 'Japanese' },
  { value: 'Korean', label: 'Korean' },
  { value: 'Mandarin', label: 'Mandarin' },
];

const MAX_VISIBLE_CHIPS = 6;

export function ThemeForm({ onTaskStart, disabled }: ThemeFormProps) {
  const [themePrompt, setThemePrompt] = useState('');
  const [sourceLang, setSourceLang] = useState('Dutch');
  const [targetLang, setTargetLang] = useState('English');
  const [wordCount, setWordCount] = useState('20');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);
  const [showAllThemes, setShowAllThemes] = useState(false);

  const queryClient = useQueryClient();

  const { data: themes } = useQuery({
    queryKey: ['themes'],
    queryFn: getThemes,
  });

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

  const handleChipClick = (theme: Theme) => {
    if (selectedTheme?.theme === theme.theme) {
      setSelectedTheme(null);
      setThemePrompt('');
      setSourceLang('Dutch');
      setTargetLang('English');
    } else {
      setSelectedTheme(theme);
      setThemePrompt(theme.theme);
      setSourceLang(theme.source_lang);
      setTargetLang(theme.target_lang);
    }
  };

  const handlePromptChange = (value: string) => {
    setThemePrompt(value);
    if (selectedTheme) {
      setSelectedTheme(null);
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
  const hasThemes = themes && themes.length > 0;
  const visibleThemes = showAllThemes ? themes : themes?.slice(0, MAX_VISIBLE_CHIPS);
  const hiddenCount = (themes?.length || 0) - MAX_VISIBLE_CHIPS;

  return (
    <Card variant="elevated" padding="lg">
      <CardHeader
        title="Generate Themed Vocabulary"
        subtitle="Create vocabulary lists for any topic and language pair"
      />

      <form onSubmit={handleSubmit} className={styles.form}>
        {hasThemes && (
          <div className={styles.existingThemes}>
            <p className={styles.existingLabel}>Expand an existing theme</p>
            <div className={styles.chipContainer}>
              {visibleThemes?.map((t) => (
                <button
                  key={t.theme}
                  type="button"
                  className={
                    selectedTheme?.theme === t.theme
                      ? styles.chipSelected
                      : styles.chip
                  }
                  aria-pressed={selectedTheme?.theme === t.theme}
                  onClick={() => handleChipClick(t)}
                  disabled={isLoading}
                >
                  <span className={styles.chipName}>{t.theme}</span>
                  <span className={styles.chipMeta}>
                    {t.word_count} words · {t.source_lang} → {t.target_lang}
                  </span>
                </button>
              ))}
              {!showAllThemes && hiddenCount > 0 && (
                <button
                  type="button"
                  className={styles.showMore}
                  onClick={() => setShowAllThemes(true)}
                >
                  +{hiddenCount} more
                </button>
              )}
            </div>
          </div>
        )}

        {hasThemes && (
          <div className={styles.divider}>or describe a new theme</div>
        )}

        <Input
          label={hasThemes ? undefined : 'Theme'}
          type="text"
          placeholder="e.g., cooking, travel, business meetings"
          value={themePrompt}
          onChange={(e) => handlePromptChange(e.target.value)}
          disabled={isLoading}
          error={error && !themePrompt.trim() ? error : undefined}
        />

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
              max="100"
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
