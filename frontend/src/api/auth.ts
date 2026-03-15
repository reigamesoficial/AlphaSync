import api from './client'
import type { LoginResponse } from '../types'

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', { email, password })
  return data
}

export async function refreshToken(token: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/refresh', { token })
  return data
}
