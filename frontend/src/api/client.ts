import type {
  TaskStatus,
  VocabularyWord,
  VocabularyStats,
  PaginatedResponse,
  Theme,
  ArticleExtractRequest,
  ThemeCreateRequest,
  SyncStatus,
  SyncRequest,
} from './types';

const API_BASE = '/api';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `Request failed: ${response.statusText}`
    );
  }

  return response.json();
}

// Tasks
export async function getTask(taskId: string): Promise<TaskStatus> {
  return request<TaskStatus>(`/tasks/${taskId}`);
}

// Vocabulary
export async function getVocabulary(
  page = 1,
  pageSize = 50,
  theme?: string
): Promise<PaginatedResponse<VocabularyWord>> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (theme) params.set('theme', theme);
  return request<PaginatedResponse<VocabularyWord>>(`/vocabulary?${params}`);
}

export async function getVocabularyStats(theme?: string): Promise<VocabularyStats> {
  const params = theme ? `?theme=${theme}` : '';
  return request<VocabularyStats>(`/vocabulary/stats${params}`);
}

export async function deleteWord(wordId: number): Promise<void> {
  await request(`/vocabulary/${wordId}`, { method: 'DELETE' });
}

// Articles
export async function extractArticle(
  data: ArticleExtractRequest
): Promise<TaskStatus> {
  return request<TaskStatus>('/articles/extract', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Themes
export async function getThemes(): Promise<Theme[]> {
  return request<Theme[]>('/themes');
}

export async function createTheme(
  data: ThemeCreateRequest
): Promise<TaskStatus> {
  return request<TaskStatus>('/themes', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Audio
export function getAudioUrl(lemma: string): string {
  return `${API_BASE}/audio/${encodeURIComponent(lemma)}.mp3`;
}

// Sync
export async function checkAnkiStatus(): Promise<SyncStatus> {
  return request<SyncStatus>('/sync/status');
}

export async function syncToAnki(data: SyncRequest): Promise<TaskStatus> {
  return request<TaskStatus>('/sync/anki', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export { ApiError };
