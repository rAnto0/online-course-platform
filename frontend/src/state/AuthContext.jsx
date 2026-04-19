import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  apiRequest,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from '../utils/apiClient.js'

const AuthContext = createContext(null)

const emptyUser = {
  id: '',
  username: '',
  email: '',
  role: 'student',
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading')

  const fetchMe = useCallback(async () => {
    const me = await apiRequest('/auth/me', { method: 'GET', auth: true })
    setUser(me)
    return me
  }, [])

  const refreshSession = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      clearTokens()
      setUser(null)
      return null
    }

    const data = await apiRequest('/auth/refresh', {
      method: 'POST',
      auth: false,
      tokenOverride: refreshToken,
    })
    setTokens(data.access_token, data.refresh_token)
    return fetchMe()
  }, [fetchMe])

  const login = useCallback(async ({ username, password }) => {
    const form = new URLSearchParams()
    form.set('username', username)
    form.set('password', password)

    const data = await apiRequest('/auth/login', {
      method: 'POST',
      auth: false,
      body: form,
      contentType: 'application/x-www-form-urlencoded',
    })

    setTokens(data.access_token, data.refresh_token)
    const me = await fetchMe()
    return me
  }, [fetchMe])

  const register = useCallback(async ({ username, email, password }) => {
    await apiRequest('/auth/register', {
      method: 'POST',
      auth: false,
      body: { username, email, password },
    })
    return login({ username, password })
  }, [login])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
    setStatus('ready')
  }, [])

  useEffect(() => {
    let mounted = true
    const init = async () => {
      try {
        const accessToken = getAccessToken()
        if (accessToken) {
          await fetchMe()
        } else if (getRefreshToken()) {
          await refreshSession()
        }
        if (mounted) {
          setStatus('ready')
        }
      } catch {
        clearTokens()
        if (mounted) {
          setUser(null)
          setStatus('ready')
        }
      }
    }
    init()
    return () => {
      mounted = false
    }
  }, [fetchMe, refreshSession])

  const value = useMemo(() => ({
    status,
    user,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
    refreshSession,
    setUser,
    safeUser: user ?? emptyUser,
  }), [status, login, register, logout, refreshSession, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
