import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import type { LoginPayload, RegisterPayload, UserProfile } from '../lib/types'
import { hasValidTokens } from '../lib/tokenStorage'
import {
  changePassword,
  fetchProfile,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  updateProfile,
} from '../lib/auth'
import { useAuth } from '../hooks/useAuth'
import { AuthContext } from '../contexts/AuthContext'

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


export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const bootstrap = async () => {
      if (!hasValidTokens()) {
        setLoading(false)
        return
      }
      try {
        const profile = await fetchProfile()
        setUser(profile)
      } catch (error) {
        console.log(error)
        logoutRequest()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    void bootstrap()
  }, [])

  const login = useCallback(async (payload: LoginPayload) => {
    await loginRequest(payload)
    const profile = await fetchProfile()
    setUser(profile)
    return profile
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    const profile = await registerRequest(payload)
    return profile
  }, [])

  const refreshProfile = useCallback(async () => {
    if (!hasValidTokens()) {
      setUser(null)
      return null
    }
    try {
      const profile = await fetchProfile()
      setUser(profile)
      return profile
    } catch (error) {
      logoutRequest()
      setUser(null)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    logoutRequest()
    setUser(null)
  }, [])

  const handleUpdate = useCallback(async (payload: Parameters<typeof updateProfile>[0]) => {
    const updated = await updateProfile(payload)
    setUser(updated)
    return updated
  }, [])

  const handleChangePassword = useCallback(
    async (payload: Parameters<typeof changePassword>[0]) => {
      const result = await changePassword(payload)
      return result
    },
    [],
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      refreshProfile,
      logout,
      update: handleUpdate,
      changePassword: handleChangePassword,
    }),
    [user, loading, login, register, refreshProfile, logout, handleUpdate, handleChangePassword],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-600">
        正在验证登录状态...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
