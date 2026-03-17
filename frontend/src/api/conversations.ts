import api from './client'
import type { Conversation, ConversationMessage, PaginatedResponse } from '../types'

export interface ListConversationsParams {
  page?: number
  per_page?: number
  status?: string
  search?: string
  assigned_to_id?: number
}

export async function listConversations(params: ListConversationsParams = {}): Promise<PaginatedResponse<Conversation>> {
  const { data } = await api.get<PaginatedResponse<Conversation>>('/conversations', { params })
  return data
}

export async function getConversation(id: number): Promise<Conversation> {
  const { data } = await api.get<Conversation>(`/conversations/${id}`)
  return data
}

export async function listConversationMessages(id: number): Promise<ConversationMessage[]> {
  const { data } = await api.get<ConversationMessage[]>(`/conversations/${id}/messages`)
  return data
}

export interface GenerateQuoteItemM2 {
  description: string
  width_m: number
  height_m: number
  quantity: number
  duration_minutes?: number
}

export interface GenerateQuoteRequestM2 {
  mode: 'm2'
  items: GenerateQuoteItemM2[]
  color?: string
  mesh?: string
  notes?: string
}

export interface GenerateQuoteRequestManual {
  mode: 'manual'
  description: string
  value: number
  duration_minutes?: number
  notes?: string
}

export interface GenerateQuoteResponse {
  quote_id: number
  total_value: number
  items_count: number
}

export async function generateQuote(
  conversationId: number,
  body: GenerateQuoteRequestM2 | GenerateQuoteRequestManual,
): Promise<GenerateQuoteResponse> {
  const { data } = await api.post<GenerateQuoteResponse>(
    `/conversations/${conversationId}/generate-quote`,
    body,
  )
  return data
}

export interface ReturnToBotResponse {
  ok: boolean
  message: string
}

export async function returnToBot(conversationId: number): Promise<ReturnToBotResponse> {
  const { data } = await api.post<ReturnToBotResponse>(
    `/conversations/${conversationId}/return-to-bot`,
  )
  return data
}

export async function techVisitConfirm(conversationId: number): Promise<ReturnToBotResponse> {
  const { data } = await api.post<ReturnToBotResponse>(
    `/conversations/${conversationId}/tech-visit-confirm`,
  )
  return data
}

export async function techVisitToQuote(conversationId: number): Promise<ReturnToBotResponse> {
  const { data } = await api.post<ReturnToBotResponse>(
    `/conversations/${conversationId}/tech-visit-to-quote`,
  )
  return data
}
