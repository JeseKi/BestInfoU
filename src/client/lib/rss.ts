// RSS API 请求封装

import api from './api'
import type {
  RSSFeedResponse,
  SourceRefreshResponse,
} from './types'

export async function fetchFeedSnapshot(limit = 50): Promise<RSSFeedResponse> {
  const { data } = await api.get<RSSFeedResponse>('/rss/feeds', {
    params: { limit },
  })
  return data
}

export async function refreshSource(sourceId: number): Promise<SourceRefreshResponse> {
  const { data } = await api.post<SourceRefreshResponse>(`/rss/sources/${sourceId}/refresh`)
  return data
}
