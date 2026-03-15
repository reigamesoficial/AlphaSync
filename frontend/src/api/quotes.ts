import api from './client'
import type { PaginatedResponse, Quote } from '../types'

export interface ListQuotesParams {
  page?: number
  per_page?: number
  status?: string
  client_id?: number
  seller_id?: number
}

export async function listQuotes(params: ListQuotesParams = {}): Promise<PaginatedResponse<Quote>> {
  const { data } = await api.get<PaginatedResponse<Quote>>('/quotes', { params })
  return data
}

export async function getQuote(id: number): Promise<Quote> {
  const { data } = await api.get<Quote>(`/quotes/${id}`)
  return data
}

export async function updateQuote(id: number, payload: Partial<Quote>): Promise<Quote> {
  const { data } = await api.patch<Quote>(`/quotes/${id}`, payload)
  return data
}
