const ACCESS_TOKEN_KEY = 'fullstack_template_access_token'
const REFRESH_TOKEN_KEY = 'fullstack_template_refresh_token'

let cachedAccessToken: string | null | undefined
let cachedRefreshToken: string | null | undefined

function isBrowser(): boolean {
  return typeof window !== 'undefined'
}

function safeRead(key: string): string | null {
  if (!isBrowser()) {
    return null
  }
  try {
    return window.localStorage.getItem(key)
  } catch (error) {
    console.log(error)
    return null
  }
}

function safeWrite(key: string, value: string | null): void {
  if (!isBrowser()) {
    return
  }
  try {
    if (value) {
      window.localStorage.setItem(key, value)
    } else {
      window.localStorage.removeItem(key)
    }
  } catch (error) {
    console.log(error)
    // 忽略存储异常，避免阻塞登录流程
  }
}

export function getAccessToken(): string | null {
  if (cachedAccessToken === undefined) {
    cachedAccessToken = safeRead(ACCESS_TOKEN_KEY)
  }
  return cachedAccessToken ?? null
}

export function getRefreshToken(): string | null {
  if (cachedRefreshToken === undefined) {
    cachedRefreshToken = safeRead(REFRESH_TOKEN_KEY)
  }
  return cachedRefreshToken ?? null
}

export function setTokens(accessToken: string | null, refreshToken: string | null): void {
  cachedAccessToken = accessToken ?? null
  cachedRefreshToken = refreshToken ?? null
  safeWrite(ACCESS_TOKEN_KEY, cachedAccessToken)
  safeWrite(REFRESH_TOKEN_KEY, cachedRefreshToken)
}

export function clearTokens(): void {
  setTokens(null, null)
}

export function hasValidTokens(): boolean {
  return Boolean(getAccessToken() && getRefreshToken())
}
