const ACCESS_TOKEN_KEY = 'ocp_access_token'
const REFRESH_TOKEN_KEY = 'ocp_refresh_token'

const fallbackBaseUrl = import.meta.env.DEV ? '/api' : 'http://localhost:8080'
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? fallbackBaseUrl

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken, refreshToken) {
  if (accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  }
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  }
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

async function parseResponse(response) {
  if (response.status === 204) {
    return null
  }
  const text = await response.text()
  if (!text) {
    return null
  }
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('No refresh token')
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${refreshToken}`,
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error('Unable to refresh token')
  }

  const data = await response.json()
  setTokens(data.access_token, data.refresh_token)
  return data.access_token
}

export async function apiRequest(
  path,
  {
    method = 'GET',
    body,
    auth = true,
    headers = {},
    contentType,
    tokenOverride,
    retry = true,
  } = {},
) {
  const finalHeaders = { Accept: 'application/json', ...headers }
  let payload = body

  if (body && !(body instanceof FormData) && !(body instanceof URLSearchParams) && typeof body === 'object') {
    payload = JSON.stringify(body)
    finalHeaders['Content-Type'] = 'application/json'
  }

  if (contentType) {
    finalHeaders['Content-Type'] = contentType
  }

  if (auth) {
    const token = tokenOverride || getAccessToken()
    if (token) {
      finalHeaders.Authorization = `Bearer ${token}`
    }
  } else if (tokenOverride) {
    finalHeaders.Authorization = `Bearer ${tokenOverride}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: finalHeaders,
    body: payload,
  })

  if (response.status === 401 && auth && retry) {
    try {
      await refreshAccessToken()
      return apiRequest(path, {
        method,
        body,
        auth,
        headers,
        contentType,
        retry: false,
      })
    } catch {
      clearTokens()
    }
  }

  if (!response.ok) {
    const data = await parseResponse(response)
    const message = data?.detail || data?.message || 'Request failed'
    const error = new Error(message)
    error.status = response.status
    error.data = data
    throw error
  }

  return parseResponse(response)
}

export function normalizeCollection(data) {
  if (Array.isArray(data)) return data
  if (data?.collection && Array.isArray(data.collection)) return data.collection
  if (data?.items && Array.isArray(data.items)) return data.items
  return []
}
