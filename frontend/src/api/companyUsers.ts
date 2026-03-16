import api from './client'

export interface CompanyUser {
  id: number
  name: string
  email: string
  role: string
  company_id: number | null
  is_active: boolean
  whatsapp_id: string | null
  created_at: string
  updated_at: string
}

export interface CompanyUserListResponse {
  items: CompanyUser[]
  total: number
  page: number
  per_page: number
}

export interface CreateCompanyUserPayload {
  name: string
  email: string
  password: string
  role: string
  is_active?: boolean
  whatsapp_id?: string | null
}

export interface UpdateCompanyUserPayload {
  name?: string
  email?: string
  role?: string
  is_active?: boolean
  password?: string
  whatsapp_id?: string | null
}

export interface ListCompanyUsersParams {
  page?: number
  per_page?: number
  search?: string
  role?: string
  is_active?: boolean
}

export async function listCompanyUsers(params: ListCompanyUsersParams = {}): Promise<CompanyUserListResponse> {
  const { data } = await api.get('/company/users', { params })
  return data
}

export async function getCompanyUser(id: number): Promise<CompanyUser> {
  const { data } = await api.get(`/company/users/${id}`)
  return data
}

export async function createCompanyUser(payload: CreateCompanyUserPayload): Promise<CompanyUser> {
  const { data } = await api.post('/company/users', payload)
  return data
}

export async function updateCompanyUser(id: number, payload: UpdateCompanyUserPayload): Promise<CompanyUser> {
  const { data } = await api.patch(`/company/users/${id}`, payload)
  return data
}
