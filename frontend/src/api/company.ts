import api from './client'
import type { CompanySettings } from '../types'

export async function getCompanySettings(): Promise<CompanySettings> {
  const { data } = await api.get<CompanySettings>('/company/settings')
  return data
}

export async function updateCompanySettings(payload: Partial<CompanySettings>): Promise<CompanySettings> {
  const { data } = await api.patch<CompanySettings>('/company/settings', payload)
  return data
}
