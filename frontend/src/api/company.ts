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

export interface InstallerScheduleConfig {
  allowed_weekdays: number[]
  work_start: string
  work_end: string
}

export interface InstallerWithSchedule {
  id: number
  name: string
  email: string
  is_active: boolean
  schedule: InstallerScheduleConfig
}

export async function listInstallers(): Promise<InstallerWithSchedule[]> {
  const { data } = await api.get<InstallerWithSchedule[]>('/company/installers')
  return data
}

export async function updateInstallerSchedule(
  userId: number,
  payload: InstallerScheduleConfig,
): Promise<InstallerWithSchedule> {
  const { data } = await api.patch<InstallerWithSchedule>(`/company/installers/${userId}/schedule`, payload)
  return data
}

export interface ScheduleConfig {
  slot_minutes: number
  workday_start: string
  workday_end: string
  allowed_weekdays: number[]
}

export async function getScheduleConfig(): Promise<ScheduleConfig> {
  const { data } = await api.get<ScheduleConfig>('/company/schedule-config')
  return data
}

export async function updateScheduleConfig(payload: ScheduleConfig): Promise<ScheduleConfig> {
  const { data } = await api.patch<ScheduleConfig>('/company/schedule-config', payload)
  return data
}

export interface DomainBotMessages {
  greeting: string
  fallback: string
  tone: string
}

export interface DomainFlowConfig {
  key: string
  display_name: string
  messages: DomainBotMessages
  is_customized: boolean
}

export async function getFlowConfig(): Promise<DomainFlowConfig[]> {
  const { data } = await api.get<DomainFlowConfig[]>('/company/flow-config')
  return data
}

export async function updateFlowConfig(key: string, messages: DomainBotMessages): Promise<DomainFlowConfig> {
  const { data } = await api.patch<DomainFlowConfig>('/company/flow-config', { key, messages })
  return data
}

export interface SlotResponse {
  start_at: string
  end_at: string
  available: boolean
}

export async function getAvailableSlots(date: string, installerId?: number): Promise<SlotResponse[]> {
  const params: Record<string, string> = { date }
  if (installerId !== undefined) params.installer_id = String(installerId)
  const { data } = await api.get<SlotResponse[]>('/appointments/slots', { params })
  return data
}

export interface CompanyProfile {
  id: number
  slug: string
  name: string
  service_domain: string
  is_active: boolean
  support_email: string | null
  support_phone: string | null
}

export async function getCompanyProfile(): Promise<CompanyProfile> {
  const { data } = await api.get<CompanyProfile>('/company/profile')
  return data
}
