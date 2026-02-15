import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteWord, getAudioUrl } from '../api/client';
import { Card } from './ui';
import type { VocabularyWord } from '../api/types';
import styles from './WordCard.module.css';

interface WordCardProps {
  word: VocabularyWord;
}

const POS_COLORS: Record<string, string> = {
  noun: 'noun',
  verb: 'verb',
  adjective: 'adjective',
  adverb: 'adverb',
  default: 'default',
};

export function WordCard({ word }: WordCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => deleteWord(word.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });

  const handlePlayAudio = async () => {
    if (isPlaying) return;

    try {
      setIsPlaying(true);
      const audio = new Audio(getAudioUrl(word.lemma));
      audioRef.current = audio;

      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => setIsPlaying(false);

      await audio.play();
    } catch {
      setIsPlaying(false);
    }
  };

  const handleDelete = () => {
    if (showConfirmDelete) {
      deleteMutation.mutate();
    } else {
      setShowConfirmDelete(true);
      setTimeout(() => setShowConfirmDelete(false), 3000);
    }
  };

  const posClass = POS_COLORS[word.pos?.toLowerCase() || ''] || POS_COLORS.default;

  return (
    <Card variant="default" padding="md" className={styles.card}>
      <div className={styles.header}>
        <div className={styles.wordInfo}>
          <h3 className={styles.lemma}>{word.lemma}</h3>
          {word.word !== word.lemma && (
            <span className={styles.word}>{word.word}</span>
          )}
        </div>
        <div className={styles.actions}>
          <button
            className={styles.audioButton}
            onClick={handlePlayAudio}
            disabled={isPlaying}
            aria-label="Play pronunciation"
            title="Play pronunciation"
          >
            {isPlaying ? (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle
                  cx="9"
                  cy="9"
                  r="7"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                  className={styles.spinningCircle}
                />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path
                  d="M3 7.5V10.5C3 11.0523 3.44772 11.5 4 11.5H6L9.5 14.5V3.5L6 6.5H4C3.44772 6.5 3 6.94772 3 7.5Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
                <path
                  d="M12 7C12.5 7.5 12.75 8.25 12.75 9C12.75 9.75 12.5 10.5 12 11"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
                <path
                  d="M14 5C15 6.2 15.5 7.55 15.5 9C15.5 10.45 15 11.8 14 13"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </button>
          <button
            className={`${styles.deleteButton} ${showConfirmDelete ? styles.confirm : ''}`}
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            aria-label={showConfirmDelete ? 'Confirm delete' : 'Delete word'}
            title={showConfirmDelete ? 'Click again to confirm' : 'Delete word'}
          >
            {showConfirmDelete ? (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path
                  d="M4 9L7.5 12.5L14 5.5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path
                  d="M3 5H15M6 5V4C6 3.44772 6.44772 3 7 3H11C11.5523 3 12 3.44772 12 4V5M14 5V14C14 14.5523 13.5523 15 13 15H5C4.44772 15 4 14.5523 4 14V5H14Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className={styles.meta}>
        {word.pos && (
          <span className={`${styles.badge} ${styles[posClass]}`}>
            {word.pos}
          </span>
        )}
        {word.gender && (
          <span className={`${styles.badge} ${styles.gender}`}>
            {word.gender}
          </span>
        )}
      </div>

      <p className={styles.translation}>{word.translation}</p>

      {word.examples.length > 0 && (
        <div className={styles.examples}>
          {word.examples.slice(0, 2).map((example, i) => (
            <p key={i} className={styles.example}>
              {example}
            </p>
          ))}
        </div>
      )}

      {word.source && (
        <p className={styles.source} title={word.source}>
          {word.theme === 'el_pais' ? 'El Pais' : word.theme}
        </p>
      )}
    </Card>
  );
}
