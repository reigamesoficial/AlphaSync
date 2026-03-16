import api from './client'
import type { PaginatedResponse } from '../types'

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

export async function getAdminMetrics(): Promise<Record<string, unknown>> {
  const { data } = await api.get('/admin/metrics')
  return data
}
