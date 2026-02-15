import type { FormEvent } from 'react';
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { extractArticle } from '../api/client';
import { Button, Input, Select, Card, CardHeader } from './ui';
import type { ArticleExtractRequest } from '../api/types';
import styles from './ArticleForm.module.css';

interface ArticleFormProps {
  onTaskStart: (taskId: string) => void;
  disabled?: boolean;
}

const BROWSER_OPTIONS = [
  { value: 'firefox', label: 'Firefox' },
  { value: 'chrome', label: 'Chrome' },
  { value: 'edge', label: 'Edge' },
  { value: 'opera', label: 'Opera' },
];

const LANGUAGE_OPTIONS = [
  { value: 'Spanish', label: 'Spanish' },
  { value: 'French', label: 'French' },
  { value: 'Italian', label: 'Italian' },
  { value: 'Portuguese', label: 'Portuguese' },
  { value: 'German', label: 'German' },
  { value: 'English', label: 'English' },
];

export function ArticleForm({ onTaskStart, disabled }: ArticleFormProps) {
  const [url, setUrl] = useState('');
  const [browser, setBrowser] = useState('firefox');
  const [sourceLang, setSourceLang] = useState('Spanish');
  const [targetLang, setTargetLang] = useState('French');
  const [wordCount, setWordCount] = useState('30');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: extractArticle,
    onSuccess: (data) => {
      onTaskStart(data.task_id);
      setUrl('');
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'Extraction failed');
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!url.trim()) {
      setError('Please enter an article URL');
      return;
    }

    const request: ArticleExtractRequest = {
      url: url.trim(),
      browser,
      source_lang: sourceLang,
      target_lang: targetLang,
      word_count: parseInt(wordCount, 10) || 30,
    };

    mutation.mutate(request);
  };

  const isLoading = mutation.isPending || disabled;

  return (
    <Card variant="elevated" padding="lg">
      <CardHeader
        title="Extract from Article"
        subtitle="Pull vocabulary from an El Pais article"
      />

      <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          label="Article URL"
          type="url"
          placeholder="https://elpais.com/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={isLoading}
          error={error && !url.trim() ? error : undefined}
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
                label="Source"
                options={LANGUAGE_OPTIONS}
                value={sourceLang}
                onChange={(e) => setSourceLang(e.target.value)}
                disabled={isLoading}
              />
              <Select
                label="Target"
                options={LANGUAGE_OPTIONS}
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className={styles.row}>
              <Select
                label="Browser"
                options={BROWSER_OPTIONS}
                value={browser}
                onChange={(e) => setBrowser(e.target.value)}
                disabled={isLoading}
              />
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
          </div>
        )}

        {error && url.trim() && <p className={styles.error}>{error}</p>}

        <Button type="submit" loading={mutation.isPending} disabled={isLoading}>
          Extract Vocabulary
        </Button>
      </form>
    </Card>
  );
}
