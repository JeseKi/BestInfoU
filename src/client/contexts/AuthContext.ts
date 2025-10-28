import { createContext } from 'react'
import type { UserProfile } from '../lib/types'

interface AuthContextValue {
  user: UserProfile | null
  loading: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<UserProfile>
  register: (payload: RegisterPayload) => Promise<UserProfile>
  refreshProfile: () => Promise<UserProfile | null>
  logout: () => void
  update: (payload: Parameters<typeof updateProfile>[0]) => Promise<UserProfile>
  changePassword: (payload: Parameters<typeof changePassword>[0]) => Promise<{ message: string }>
}

// 注意：这里需要导入相关类型
import type { LoginPayload, RegisterPayload } from '../lib/types'
import type { updateProfile, changePassword } from '../lib/auth'

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export { AuthContext }
