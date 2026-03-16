import { useEffect, useState, useCallback, useRef } from 'react'
import {
  MessageSquare, Search, ChevronLeft, ChevronRight, Clock,
  X, Download, FileText, Image as ImageIcon, Video, File,
  ExternalLink, Send, Bot, User as UserIcon,
} from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import { PageSpinner } from '../components/ui/Spinner'
import { listConversations, listConversationMessages, getConversation } from '../api/conversations'
import type { Conversation, ConversationMessage, PaginatedResponse } from '../types'

const STATUSES = ['', 'open', 'bot', 'assumed', 'closed', 'archived']
const STATUS_LABELS: Record<string, string> = {
  '': 'Todas', open: 'Abertas', bot: 'Bot', assumed: 'Assumidas', closed: 'Fechadas', archived: 'Arquivadas',
}

function timeAgo(date: string | null): string {
  if (!date) return '—'
  const diff = Date.now() - new Date(date).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 60) return `${m}min atrás`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h atrás`
  return `${Math.floor(h / 24)}d atrás`
}

function formatTime(date: string): string {
  return new Date(date).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}

const CHANNEL_LABELS: Record<string, string> = {
  whatsapp: 'WhatsApp', webchat: 'Web Chat', instagram: 'Instagram',
}

type MediaKind = 'image' | 'video' | 'pdf' | 'audio' | 'document' | 'text'

function detectMediaKind(msg: ConversationMessage): MediaKind {
  const url = (msg.media_url || '').toLowerCase()
  const type = (msg.type || '').toLowerCase()

  if (type === 'image' || /\.(jpg|jpeg|png|gif|webp|svg)(\?|$)/.test(url)) return 'image'
  if (type === 'video' || /\.(mp4|webm|mov|avi)(\?|$)/.test(url)) return 'video'
  if (type === 'audio' || /\.(mp3|ogg|wav|m4a|aac)(\?|$)/.test(url)) return 'audio'
  if (type === 'document' && url.endsWith('.pdf')) return 'pdf'
  if (type === 'document') return 'document'
  if (url.includes('.pdf')) return 'pdf'
  if (url) return 'document'
  return 'text'
}

function MediaPreview({ msg }: { msg: ConversationMessage }) {
  const kind = detectMediaKind(msg)
  const url = msg.media_url || ''

  const DownloadBtn = ({ label = 'Baixar' }: { label?: string }) => (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 mt-1.5"
      download
    >
      <Download className="w-3 h-3" />
      {label}
    </a>
  )

  if (kind === 'image') {
    return (
      <div className="mt-1">
        <a href={url} target="_blank" rel="noopener noreferrer">
          <img
            src={url}
            alt="imagem"
            className="max-w-[220px] max-h-[180px] rounded-lg object-cover border border-surface-600 hover:opacity-90 transition-opacity"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        </a>
        <DownloadBtn label="Baixar imagem" />
      </div>
    )
  }

  if (kind === 'video') {
    return (
      <div className="mt-1">
        <video
          src={url}
          controls
          className="max-w-[240px] rounded-lg border border-surface-600"
          style={{ maxHeight: 160 }}
        />
        <DownloadBtn label="Baixar vídeo" />
      </div>
    )
  }

  if (kind === 'audio') {
    return (
      <div className="mt-1">
        <audio src={url} controls className="w-[220px]" />
        <DownloadBtn label="Baixar áudio" />
      </div>
    )
  }

  if (kind === 'pdf') {
    return (
      <div className="mt-1 border border-surface-600 rounded-lg overflow-hidden bg-surface-800">
        <iframe
          src={`${url}#view=FitH`}
          title="PDF"
          className="w-[280px] h-[200px]"
          style={{ border: 'none' }}
        />
        <div className="flex items-center gap-2 px-2 py-1.5 border-t border-surface-600">
          <FileText className="w-3.5 h-3.5 text-red-400 shrink-0" />
          <span className="text-xs text-slate-400 truncate flex-1">Documento PDF</span>
          <a href={url} target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:text-brand-300">
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-1 flex items-center gap-2 bg-surface-700 rounded-lg px-3 py-2 border border-surface-600">
      <File className="w-4 h-4 text-slate-400 shrink-0" />
      <span className="text-xs text-slate-300 truncate max-w-[160px]">
        {url.split('/').pop() || 'Arquivo'}
      </span>
      <DownloadBtn label="" />
    </div>
  )
}

function MessageBubble({ msg }: { msg: ConversationMessage }) {
  const isOut = msg.direction === 'out'
  const hasMedia = !!msg.media_url
  const hasText = !!msg.content

  return (
    <div className={`flex gap-2 ${isOut ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
        isOut ? 'bg-brand-600/20' : 'bg-emerald-600/20'
      }`}>
        {isOut
          ? <Bot className="w-3 h-3 text-brand-400" />
          : <UserIcon className="w-3 h-3 text-emerald-400" />
        }
      </div>
      <div className={`max-w-[75%] ${isOut ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`rounded-2xl px-3 py-2 text-sm ${
          isOut
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-surface-700 text-slate-200 rounded-tl-sm border border-surface-600'
        }`}>
          {hasText && (
            <p className="whitespace-pre-wrap break-words leading-relaxed">{msg.content}</p>
          )}
          {hasMedia && <MediaPreview msg={msg} />}
          {!hasText && !hasMedia && (
            <span className="text-slate-400 text-xs italic">mensagem sem conteúdo</span>
          )}
        </div>
        <span className="text-slate-600 text-[10px] mt-0.5 px-1">
          {formatTime(msg.created_at)}
          {msg.sender_name && !isOut && (
            <span className="text-slate-600"> · {msg.sender_name}</span>
          )}
        </span>
      </div>
    </div>
  )
}

function DateSeparator({ date }: { date: string }) {
  return (
    <div className="flex items-center gap-3 my-3">
      <div className="flex-1 h-px bg-surface-600" />
      <span className="text-slate-600 text-[10px] font-medium shrink-0">
        {formatDate(date)}
      </span>
      <div className="flex-1 h-px bg-surface-600" />
    </div>
  )
}

function ChatDrawer({
  conv,
  onClose,
}: {
  conv: Conversation
  onClose: () => void
}) {
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setLoading(true)
    listConversationMessages(conv.id)
      .then((msgs) => setMessages(msgs))
      .catch(() => setMessages([]))
      .finally(() => setLoading(false))
  }, [conv.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Group messages by date
  const groups: { date: string; msgs: ConversationMessage[] }[] = []
  for (const msg of messages) {
    const day = msg.created_at.slice(0, 10)
    const last = groups[groups.length - 1]
    if (last && last.date === day) {
      last.msgs.push(msg)
    } else {
      groups.push({ date: day, msgs: [msg] })
    }
  }

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex flex-col w-full max-w-md bg-surface-800 border-l border-surface-600 shadow-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-surface-600 bg-surface-700">
        <div className="w-9 h-9 rounded-full bg-emerald-600/20 flex items-center justify-center shrink-0">
          <MessageSquare className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium text-sm truncate">{conv.phone}</p>
          <div className="flex items-center gap-2">
            <Badge value={conv.status} />
            {conv.bot_step && (
              <code className="text-[10px] text-violet-400 bg-violet-500/10 px-1.5 py-0.5 rounded">
                {conv.bot_step}
              </code>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="btn-ghost p-1.5 shrink-0"
          aria-label="Fechar"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Metadata strip */}
      {conv.subject && (
        <div className="px-4 py-1.5 bg-surface-750 border-b border-surface-600">
          <p className="text-xs text-slate-500 truncate">{conv.subject}</p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-6 h-6 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-slate-600">
            <MessageSquare className="w-8 h-8" />
            <p className="text-sm">Nenhuma mensagem ainda</p>
          </div>
        ) : (
          <>
            {groups.map((group) => (
              <div key={group.date}>
                <DateSeparator date={group.date} />
                <div className="space-y-2">
                  {group.msgs.map((msg) => (
                    <MessageBubble key={msg.id} msg={msg} />
                  ))}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Footer info */}
      <div className="px-4 py-2.5 border-t border-surface-600 bg-surface-700">
        <div className="flex items-center justify-between">
          <span className="text-slate-600 text-xs flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Última msg {timeAgo(conv.last_message_at)}
          </span>
          <span className="text-slate-600 text-xs">
            {CHANNEL_LABELS[conv.channel] ?? conv.channel}
          </span>
        </div>
        <p className="text-slate-700 text-[10px] mt-0.5">
          {messages.length} mensagem{messages.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  )
}

export default function Conversations() {
  const [data, setData] = useState<PaginatedResponse<Conversation> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null)
  const perPage = 20

  const fetchConversations = useCallback(async () => {
    setLoading(true)
    try {
      const result = await listConversations({
        page,
        per_page: perPage,
        search: search || undefined,
        status: status || undefined,
      })
      setData(result)
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [page, search, status])

  useEffect(() => { setPage(1) }, [search, status])
  useEffect(() => { fetchConversations() }, [fetchConversations])

  const totalPages = data ? Math.ceil(data.total / perPage) : 0

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title="Conversas" subtitle={data ? `${data.total} registros` : ''} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                className="input pl-9"
                placeholder="Buscar por telefone ou assunto..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {STATUSES.map((s) => (
                <button
                  key={s}
                  onClick={() => setStatus(s)}
                  className={`shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    status === s
                      ? 'bg-brand-600 text-white'
                      : 'bg-surface-700 text-slate-400 hover:text-white hover:bg-surface-600'
                  }`}
                >
                  {STATUS_LABELS[s]}
                </button>
              ))}
            </div>
          </div>

          <div className="card overflow-hidden">
            {loading ? (
              <PageSpinner />
            ) : !data || data.items.length === 0 ? (
              <EmptyState
                icon={<MessageSquare className="w-10 h-10" />}
                title="Nenhuma conversa encontrada"
                description="Conversas via WhatsApp aparecerão aqui automaticamente."
              />
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-surface-600">
                        <th className="text-left text-slate-500 font-medium px-5 py-3">Telefone / Assunto</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3">Status</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden md:table-cell">Canal</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden lg:table-cell">Etapa bot</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden sm:table-cell">Última msg</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-700">
                      {data.items.map((conv) => (
                        <tr
                          key={conv.id}
                          onClick={() => setSelectedConv(conv)}
                          className={`hover:bg-surface-700/30 transition-colors cursor-pointer ${
                            selectedConv?.id === conv.id ? 'bg-brand-600/5 border-l-2 border-brand-500' : ''
                          }`}
                        >
                          <td className="px-5 py-3.5">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-emerald-600/20 flex items-center justify-center shrink-0">
                                <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                              </div>
                              <div className="min-w-0">
                                <p className="text-white font-medium">{conv.phone}</p>
                                {conv.subject && (
                                  <p className="text-slate-500 text-xs truncate max-w-48">{conv.subject}</p>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-3.5"><Badge value={conv.status} /></td>
                          <td className="px-5 py-3.5 hidden md:table-cell">
                            <span className="text-slate-400 text-xs">{CHANNEL_LABELS[conv.channel] ?? conv.channel}</span>
                          </td>
                          <td className="px-5 py-3.5 hidden lg:table-cell">
                            {conv.bot_step ? (
                              <code className="text-xs text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded">
                                {conv.bot_step}
                              </code>
                            ) : (
                              <span className="text-slate-600 text-xs">—</span>
                            )}
                          </td>
                          <td className="px-5 py-3.5 hidden sm:table-cell">
                            <span className="flex items-center gap-1 text-slate-400 text-xs">
                              <Clock className="w-3 h-3" />
                              {timeAgo(conv.last_message_at)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {totalPages > 1 && (
                  <div className="flex items-center justify-between px-5 py-3 border-t border-surface-600">
                    <p className="text-slate-500 text-sm">
                      Mostrando {(page - 1) * perPage + 1}–{Math.min(page * perPage, data.total)} de {data.total}
                    </p>
                    <div className="flex gap-2">
                      <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn-ghost p-1.5 disabled:opacity-40">
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <span className="text-slate-400 text-sm px-2 py-1.5">{page} / {totalPages}</span>
                      <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-ghost p-1.5 disabled:opacity-40">
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>

      {/* Chat Drawer overlay */}
      {selectedConv && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
            onClick={() => setSelectedConv(null)}
          />
          <ChatDrawer conv={selectedConv} onClose={() => setSelectedConv(null)} />
        </>
      )}
    </div>
  )
}
