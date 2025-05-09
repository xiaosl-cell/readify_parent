const TOKEN_KEY = 'readify_token'

export const getToken = (): string => {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

export const getAuthHeader = (): string => {
  const token = getToken()
  return token ? `Bearer ${token}` : ''
} 