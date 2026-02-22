import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getThemes } from '../api/client';
import { Input } from './ui';
import type { Theme } from '../api/types';
import styles from './ThemeSelector.module.css';

const MAX_VISIBLE_CHIPS = 6;

interface ThemeSelectorProps {
  value: string;
  onChange: (value: string) => void;
  onThemeSelect: (theme: Theme | null) => void;
  selectedTheme: Theme | null;
  disabled?: boolean;
}

export function ThemeSelector({
  value,
  onChange,
  onThemeSelect,
  selectedTheme,
  disabled,
}: ThemeSelectorProps) {
  const [showAllThemes, setShowAllThemes] = useState(false);

  const { data: themes } = useQuery({
    queryKey: ['themes'],
    queryFn: getThemes,
  });

  const hasThemes = themes && themes.length > 0;
  const visibleThemes = showAllThemes ? themes : themes?.slice(0, MAX_VISIBLE_CHIPS);
  const hiddenCount = (themes?.length || 0) - MAX_VISIBLE_CHIPS;

  const handleChipClick = (theme: Theme) => {
    if (selectedTheme?.theme === theme.theme) {
      onThemeSelect(null);
      onChange('');
    } else {
      onThemeSelect(theme);
      onChange(theme.theme);
    }
  };

  const handleInputChange = (inputValue: string) => {
    onChange(inputValue);
    if (selectedTheme) {
      onThemeSelect(null);
    }
  };

  return (
    <>
      {hasThemes && (
        <div className={styles.existingThemes}>
          <p className={styles.existingLabel}>Select an existing theme</p>
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
                disabled={disabled}
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
        value={value}
        onChange={(e) => handleInputChange(e.target.value)}
        disabled={disabled}
      />
    </>
  );
}
