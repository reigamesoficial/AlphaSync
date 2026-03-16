import api from './client'
import type { PaginatedResponse } from '../types'

// ============================================================
// COMPANIES
// ============================================================

export interface CompanyListItem {
  id: number
  slug: string
  name: string
  status: string
  service_domain: string
  plan_name: string | null
  whatsapp_phone_number_id: string | null
  whatsapp_business_account_id: string | null
  support_email: string | null
  support_phone: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  user_count: number
  has_settings: boolean
  has_admin: boolean
}

export interface AdminUserSummary {
  id: number
  name: string
  email: string
  role: string
  is_active: boolean
}

export interface CompanySettings {
  id: number
  company_id: number
  brand_name: string | null
  bot_name: string | null
  quote_prefix: string | null
  currency: string
  timezone: string
  extra_settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface CompanyDetail extends CompanyListItem {
  settings: CompanySettings | null
  admin_users: AdminUserSummary[]
}

export interface CreateCompanyPayload {
  name: string
  slug: string
  service_domain: string
  plan_name?: string
  whatsapp_phone_number_id?: string
  support_email?: string
  admin_name: string
  admin_email: string
  admin_password: string
}

export interface UpdateCompanyPayload {
  name?: string
  status?: string
  plan_name?: string
  is_active?: boolean
  service_domain?: string
  whatsapp_phone_number_id?: string
  support_email?: string
}

export interface BootstrapAdminPayload {
  admin_name: string
  admin_email: string
  admin_password: string
}

export interface ListCompaniesParams {
  page?: number
  per_page?: number
  search?: string
  is_active?: boolean
}

export async function listCompanies(params: ListCompaniesParams = {}): Promise<PaginatedResponse<CompanyListItem>> {
  const { data } = await api.get<PaginatedResponse<CompanyListItem>>('/admin/companies', { params })
  return data
}

export async function getCompany(id: number): Promise<CompanyDetail> {
  const { data } = await api.get<CompanyDetail>(`/admin/companies/${id}`)
  return data
}

export async function createCompany(payload: CreateCompanyPayload): Promise<CompanyDetail> {
  const { data } = await api.post<CompanyDetail>('/admin/companies', payload)
  return data
}

export async function updateCompany(id: number, payload: UpdateCompanyPayload): Promise<CompanyDetail> {
  const { data } = await api.patch<CompanyDetail>(`/admin/companies/${id}`, payload)
  return data
}

export async function bootstrapAdmin(id: number, payload: BootstrapAdminPayload): Promise<CompanyDetail> {
  const { data } = await api.post<CompanyDetail>(`/admin/companies/${id}/bootstrap-admin`, payload)
  return data
}

// ============================================================
// USERS
// ============================================================

export interface AdminUser {
  id: number
  name: string
  email: string
  role: string
  company_id: number | null
  company_name: string | null
  company_slug: string | null
  whatsapp_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ListUsersParams {
  page?: number
  per_page?: number
  search?: string
  role?: string
  company_id?: number
  is_active?: boolean
}

export interface CreateUserPayload {
  name: string
  email: string
  password: string
  role: string
  company_id: number | null
  is_active?: boolean
}

export interface UpdateUserPayload {
  name?: string
  email?: string
  role?: string
  company_id?: number | null
  is_active?: boolean
  password?: string
}

export async function listUsers(params: ListUsersParams = {}): Promise<PaginatedResponse<AdminUser>> {
  const { data } = await api.get<PaginatedResponse<AdminUser>>('/admin/users', { params })
  return data
}

export async function getUser(id: number): Promise<AdminUser> {
  const { data } = await api.get<AdminUser>(`/admin/users/${id}`)
  return data
}

export async function createUser(payload: CreateUserPayload): Promise<AdminUser> {
  const { data } = await api.post<AdminUser>('/admin/users', payload)
  return data
}

export async function updateUser(id: number, payload: UpdateUserPayload): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/admin/users/${id}`, payload)
  return data
}

// ============================================================
// PLATFORM SETTINGS
// ============================================================

export interface PlatformSettings {
  id: number
  platform_name: string
  default_company_plan: string | null
  default_service_domain: string
  allow_self_signup: boolean
  support_email: string | null
  support_phone: string | null
  public_app_url: string | null
  logo_url: string | null
  extra_flags: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type UpdatePlatformSettingsPayload = Partial<Omit<PlatformSettings, 'id' | 'created_at' | 'updated_at'>>

export async function getPlatformSettings(): Promise<PlatformSettings> {
  const { data } = await api.get<PlatformSettings>('/admin/settings')
  return data
}

export async function updatePlatformSettings(payload: UpdatePlatformSettingsPayload): Promise<PlatformSettings> {
  const { data } = await api.patch<PlatformSettings>('/admin/settings', payload)
  return data
}

// ============================================================
// METRICS
// ============================================================

export async function getAdminMetrics(): Promise<Record<string, unknown>> {
  const { data } = await api.get('/admin/metrics')
  return data
}

// ============================================================
// DOMAIN DEFINITIONS
// ============================================================

export interface DomainDefinitionListItem {
  id: number
  key: string
  display_name: string
  description: string | null
  icon: string | null
  is_active: boolean
  is_builtin: boolean
  created_at: string
  updated_at: string
}

export interface DomainDefinitionDetail extends DomainDefinitionListItem {
  config_json: Record<string, unknown>
}

export interface UpdateDomainPayload {
  display_name?: string
  description?: string | null
  icon?: string | null
  is_active?: boolean
  config_json?: Record<string, unknown>
}

export interface DomainSyncResult {
  synced: number
  created: number
  skipped: number
  keys: string[]
}

export async function listDomains(): Promise<DomainDefinitionListItem[]> {
  const { data } = await api.get<DomainDefinitionListItem[]>('/admin/domains')
  return data
}

export async function getDomain(key: string): Promise<DomainDefinitionDetail> {
  const { data } = await api.get<DomainDefinitionDetail>(`/admin/domains/${key}`)
  return data
}

export async function updateDomain(key: string, payload: UpdateDomainPayload): Promise<DomainDefinitionDetail> {
  const { data } = await api.put<DomainDefinitionDetail>(`/admin/domains/${key}`, payload)
  return data
}

export async function syncDomains(): Promise<DomainSyncResult> {
  const { data } = await api.post<DomainSyncResult>('/admin/domains/sync')
  return data
}
