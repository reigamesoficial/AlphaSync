import api from './client'
import type { Client, PaginatedResponse } from '../types'

export interface ListClientsParams {
  page?: number
  per_page?: number
  search?: string
  status?: string
  lead_source?: string
}

export async function listClients(params: ListClientsParams = {}): Promise<PaginatedResponse<Client>> {
  const { data } = await api.get<PaginatedResponse<Client>>('/clients', { params })
  return data
}

export async function getClient(id: number): Promise<Client> {
  const { data } = await api.get<Client>(`/clients/${id}`)
  return data
}

export async function createClient(payload: Partial<Client>): Promise<Client> {
  const { data } = await api.post<Client>('/clients', payload)
  return data
}

export async function updateClient(id: number, payload: Partial<Client>): Promise<Client> {
  const { data } = await api.patch<Client>(`/clients/${id}`, payload)
  return data
}
