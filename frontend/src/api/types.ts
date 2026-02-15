// Task types
export type TaskType = 'article_extract' | 'theme_create' | 'audio_generate' | 'anki_sync';
export type TaskStatusEnum = 'pending' | 'in_progress' | 'completed' | 'failed';

export interface TaskStatus {
  task_id: string;
  type: TaskType;
  status: TaskStatusEnum;
  progress?: string;
  result?: unknown;
  error?: string;
  created_at: string;
  completed_at?: string;
}

// Vocabulary types
export interface VocabularyWord {
  id: number;
  word: string;
  lemma: string;
  pos?: string;
  gender?: string;
  translation: string;
  source_lang?: string;
  target_lang?: string;
  examples: string[];
  source?: string;
  theme: string;
  added_at?: string;
}

export interface VocabularyStats {
  total_words: number;
  by_pos: Record<string, number>;
  by_theme: Record<string, number>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Theme types
export interface Theme {
  id: number;
  table_name: string;
  theme_description: string;
  source_lang: string;
  target_lang: string;
  deck_name: string;
  created_at?: string;
  word_count: number;
}

export interface ThemeWord {
  id: number;
  word: string;
  lemma: string;
  pos?: string;
  translation: string;
  examples: string[];
  added_at?: string;
}

export interface ThemeWithWords {
  theme: Theme;
  words: ThemeWord[];
}

// Request types
export interface ArticleExtractRequest {
  url: string;
  browser?: string;
  source_lang?: string;
  target_lang?: string;
  word_count?: number;
  prompt?: string;
}

export interface ThemeCreateRequest {
  theme_prompt: string;
  source_lang?: string;
  target_lang?: string;
  word_count?: number;
  deck_name?: string;
}

// Result types
export interface ArticleExtractResult {
  new_words: number;
  updated_words: number;
  words: Record<string, unknown>[];
  source_url: string;
}

export interface ThemeCreateResult {
  table_name: string;
  theme_description: string;
  new_words: number;
  updated_words: number;
  is_related_theme: boolean;
  related_theme_name?: string;
}

// Sync types
export interface SyncStatus {
  anki_connected: boolean;
  error?: string;
}

export interface SyncRequest {
  include_main?: boolean;
  include_themes?: boolean;
  theme_names?: string[];
}

export interface SyncResult {
  total_added: number;
  total_skipped: number;
  decks_synced: string[];
}
