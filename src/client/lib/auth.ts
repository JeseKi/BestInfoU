import api from './api'
import { setTokens, clearTokens } from './tokenStorage'
import type {
  LoginPayload,
  PasswordChangePayload,
  RegisterPayload,
  TokenResponse,
  UpdateProfilePayload,
  UserProfile,
} from './types'

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  console.log('【Auth API】准备发送登录请求', { 用户名: payload.username })
  const { data } = await api.post<TokenResponse>('/auth/login', payload)
  console.log('【Auth API】登录请求返回', { tokenType: data.token_type })
  setTokens(data.access_token, data.refresh_token)
  return data
}

export async function register(payload: RegisterPayload): Promise<UserProfile> {
  const { data } = await api.post<UserProfile>('/auth/register', payload)
  return data
}

export async function fetchProfile(): Promise<UserProfile> {
  const { data } = await api.get<UserProfile>('/auth/profile')
  return data
}

export async function updateProfile(payload: UpdateProfilePayload): Promise<UserProfile> {
  const { data } = await api.put<UserProfile>('/auth/profile', payload)
  return data
}

export async function changePassword(payload: PasswordChangePayload): Promise<{ message: string }> {
  const { data } = await api.put<{ message: string }>('/auth/password', payload)
  return data
}

export function logout(): void {
  clearTokens()
}
