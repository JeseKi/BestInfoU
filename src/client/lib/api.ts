import axios, { type AxiosError, type AxiosRequestConfig } from 'axios'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './tokenStorage'
import type { TokenResponse } from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
})

let refreshRequest: Promise<string | null> | null = null

function cleanupBaseUrl(url: string | undefined): string {
  if (!url) {
    return ''
  }
  if (url.endsWith('/')) {
    return url.slice(0, -1)
  }
  return url
}

function shouldSkipRefresh(url?: string): boolean {
  if (!url) {
    return false
  }
  const blocked = ['/auth/login', '/auth/register', '/auth/refresh']
  return blocked.some((path) => url.includes(path))
}

async function requestRefreshToken(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return null
  }

  const baseUrl = cleanupBaseUrl(api.defaults.baseURL)
  try {
    const response = await axios.post<TokenResponse>(
      `${baseUrl}/auth/refresh`,
      null,
      {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      },
    )

    const { access_token: accessToken, refresh_token: newRefreshToken } = response.data
    setTokens(accessToken, newRefreshToken)
    return accessToken
  } catch (error) {
    clearTokens()
    throw error
  }
}

type RetryableConfig = AxiosRequestConfig & { _retry?: boolean }

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const originalRequest = error.config as RetryableConfig | undefined

    if (status === 401 && originalRequest && !originalRequest._retry && !shouldSkipRefresh(originalRequest.url)) {
      originalRequest._retry = true

      try {
        refreshRequest = refreshRequest ?? requestRefreshToken()
        const newAccessToken = await refreshRequest
        refreshRequest = null

        if (!newAccessToken) {
          throw error
        }

        originalRequest.headers = originalRequest.headers ?? {}
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        refreshRequest = null
        clearTokens()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)

export default api
