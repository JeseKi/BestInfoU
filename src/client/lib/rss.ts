// RSS API 请求封装

import api from './api'
import type {
  RSSFeedResponse,
  SourceRefreshResponse,
  RSSSource,
  CreateSourcePayload,
  UpdateSourcePayload,
} from './types'

export async function fetchFeedSnapshot(limit = 50): Promise<RSSFeedResponse> {
  const { data } = await api.get<RSSFeedResponse>('/rss/feeds', {
    params: { limit },
  })
  return data
}

export async function fetchSources(): Promise<RSSSource[]> {
  const { data } = await api.get<RSSSource[]>('/rss/sources')
  return data
}

export async function createSource(payload: CreateSourcePayload): Promise<RSSSource> {
  const { data } = await api.post<RSSSource>('/rss/sources', payload)
  return data
}

export async function updateSource(
  sourceId: number,
  payload: UpdateSourcePayload,
): Promise<RSSSource> {
  const { data } = await api.patch<RSSSource>(`/rss/sources/${sourceId}`, payload)
  return data
}

export async function deleteSource(sourceId: number): Promise<void> {
  await api.delete(`/rss/sources/${sourceId}`)
}

export async function refreshSource(sourceId: number): Promise<SourceRefreshResponse> {
  const { data } = await api.post<SourceRefreshResponse>(`/rss/sources/${sourceId}/refresh`)
  return data
}
