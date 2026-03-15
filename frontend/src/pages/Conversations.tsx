import { useEffect, useState, useCallback } from 'react'
import { MessageSquare, Search, ChevronLeft, ChevronRight, Clock } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import { PageSpinner } from '../components/ui/Spinner'
import { listConversations } from '../api/conversations'
import type { Conversation, PaginatedResponse } from '../types'

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

const CHANNEL_LABELS: Record<string, string> = { whatsapp: 'WhatsApp', webchat: 'Web Chat', instagram: 'Instagram' }

export default function Conversations() {
  const [data, setData] = useState<PaginatedResponse<Conversation> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
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
                        <tr key={conv.id} className="hover:bg-surface-700/30 transition-colors">
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
    </div>
  )
}
