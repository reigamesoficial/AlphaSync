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
