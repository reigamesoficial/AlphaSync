import { useEffect, useState, useCallback } from 'react'
import { FileText, ChevronLeft, ChevronRight } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import { PageSpinner } from '../components/ui/Spinner'
import { listQuotes } from '../api/quotes'
import type { PaginatedResponse, Quote } from '../types'

const STATUSES = ['', 'draft', 'confirmed', 'done', 'cancelled', 'expired']
const STATUS_LABELS: Record<string, string> = {
  '': 'Todos', draft: 'Rascunho', confirmed: 'Confirmado', done: 'Concluído',
  cancelled: 'Cancelado', expired: 'Expirado',
}

function formatCurrency(value: string): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(value))
}

export default function Quotes() {
  const [data, setData] = useState<PaginatedResponse<Quote> | null>(null)
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 20

  const fetchQuotes = useCallback(async () => {
    setLoading(true)
    try {
      const result = await listQuotes({
        page,
        per_page: perPage,
        status: status || undefined,
      })
      setData(result)
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [page, status])

  useEffect(() => { setPage(1) }, [status])
  useEffect(() => { fetchQuotes() }, [fetchQuotes])

  const totalPages = data ? Math.ceil(data.total / perPage) : 0

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title="Orçamentos" subtitle={data ? `${data.total} registros` : ''} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl space-y-4">
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

          <div className="card overflow-hidden">
            {loading ? (
              <PageSpinner />
            ) : !data || data.items.length === 0 ? (
              <EmptyState
                icon={<FileText className="w-10 h-10" />}
                title="Nenhum orçamento encontrado"
                description="Orçamentos gerados pelo bot ou manualmente aparecerão aqui."
              />
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-surface-600">
                        <th className="text-left text-slate-500 font-medium px-5 py-3">#</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3">Título</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3">Status</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden md:table-cell">Serviço</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden lg:table-cell">Itens</th>
                        <th className="text-right text-slate-500 font-medium px-5 py-3">Total</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden xl:table-cell">Data</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-700">
                      {data.items.map((q) => (
                        <tr key={q.id} className="hover:bg-surface-700/30 transition-colors">
                          <td className="px-5 py-3.5">
                            <span className="text-slate-500 font-mono text-xs">#{q.id}</span>
                            {q.code && (
                              <p className="text-slate-600 font-mono text-[10px]">{q.code}</p>
                            )}
                          </td>
                          <td className="px-5 py-3.5">
                            <p className="text-white font-medium truncate max-w-48">
                              {q.title ?? `Orçamento #${q.id}`}
                            </p>
                            {q.description && (
                              <p className="text-slate-500 text-xs truncate max-w-48">{q.description}</p>
                            )}
                          </td>
                          <td className="px-5 py-3.5"><Badge value={q.status} /></td>
                          <td className="px-5 py-3.5 hidden md:table-cell">
                            <span className="text-slate-400 text-xs capitalize">{q.service_type.replace('_', ' ')}</span>
                          </td>
                          <td className="px-5 py-3.5 hidden lg:table-cell">
                            <span className="text-slate-400 text-xs">{q.items?.length ?? 0} itens</span>
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <span className="text-white font-semibold text-sm">
                              {formatCurrency(q.total_value)}
                            </span>
                            {parseFloat(q.discount) > 0 && (
                              <p className="text-slate-500 text-xs">- {formatCurrency(q.discount)}</p>
                            )}
                          </td>
                          <td className="px-5 py-3.5 hidden xl:table-cell text-slate-400 text-xs">
                            {new Date(q.created_at).toLocaleDateString('pt-BR')}
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
