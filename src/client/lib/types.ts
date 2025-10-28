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
