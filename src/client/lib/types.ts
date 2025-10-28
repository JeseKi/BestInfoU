export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
}

export interface UserProfile {
  id: number
  username: string
  email: string
  name: string | null
  role: string
  status: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface UpdateProfilePayload {
  email?: string | null
  name?: string | null
}

export interface PasswordChangePayload {
  old_password: string
  new_password: string
}

export interface ItemPayload {
  name: string
}

export interface Item {
  id: number
  name: string
}

export interface RSSSource {
  id: number
  name: string
  feed_url: string
  homepage_url: string | null
  feed_avatar: string | null
  description: string | null
  language: string | null
  category: string | null
  is_active: boolean
  sync_interval_minutes: number
  last_synced_at: string | null
}

export interface RSSEntry {
  id: number
  source_id: number
  source_name: string
  feed_avatar: string | null
  title: string
  summary: string | null
  content: string | null
  link: string | null
  author: string | null
  published_at: string | null
  fetched_at: string
}

export interface FetchLog {
  id: number
  source_id: number
  status: string
  started_at: string
  finished_at: string | null
  error_message: string | null
  entries_fetched: number
}

export interface RSSFeedResponse {
  sources: RSSSource[]
  entries: RSSEntry[]
}

export interface SourceRefreshResponse {
  source: RSSSource
  fetch_log: FetchLog
}
