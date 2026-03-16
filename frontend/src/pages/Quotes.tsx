import { useEffect, useState, useCallback, useRef } from 'react'
import {
  FileText, ChevronLeft, ChevronRight, X, Download, FilePlus2,
  User, Phone, CheckCircle2, XCircle, Clock, AlertCircle,
} from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import { PageSpinner } from '../components/ui/Spinner'
import { listQuotes, getQuote, updateQuote, generatePdf, downloadQuotePdf } from '../api/quotes'
import type { PaginatedResponse, Quote } from '../types'

const STATUSES = ['', 'draft', 'confirmed', 'done', 'cancelled', 'expired']
const STATUS_LABELS: Record<string, string> = {
  '': 'Todos', draft: 'Rascunho', confirmed: 'Confirmado',
  done: 'Concluído', cancelled: 'Cancelado', expired: 'Expirado',
}

function fmt(value: string): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(value) || 0)
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR')
}

function dimM(cm: string | null): string {
  if (!cm) return '—'
  return (parseFloat(cm) / 100).toFixed(2).replace('.', ',')
}

function areaM2(wCm: string | null, hCm: string | null, qty: number): string {
  if (!wCm || !hCm) return '—'
  const a = (parseFloat(wCm) / 100) * (parseFloat(hCm) / 100) * qty
  return a.toFixed(2).replace('.', ',') + ' m²'
}

interface Toast { msg: string; type: 'success' | 'error' }

interface StatusAction { label: string; nextStatus: Quote['status']; color: string }

function getStatusActions(status: Quote['status']): StatusAction[] {
  if (status === 'draft') {
    return [
      { label: 'Confirmar', nextStatus: 'confirmed', color: 'bg-emerald-600 hover:bg-emerald-500' },
      { label: 'Cancelar', nextStatus: 'cancelled', color: 'bg-red-700 hover:bg-red-600' },
    ]
  }
  if (status === 'confirmed') {
    return [
      { label: 'Concluir', nextStatus: 'done', color: 'bg-emerald-600 hover:bg-emerald-500' },
      { label: 'Cancelar', nextStatus: 'cancelled', color: 'bg-red-700 hover:bg-red-600' },
    ]
  }
  return []
}

function StatusIcon({ status }: { status: Quote['status'] }) {
  if (status === 'done') return <CheckCircle2 className="w-4 h-4 text-emerald-400" />
  if (status === 'confirmed') return <Clock className="w-4 h-4 text-blue-400" />
  if (status === 'cancelled') return <XCircle className="w-4 h-4 text-red-400" />
  if (status === 'expired') return <AlertCircle className="w-4 h-4 text-slate-400" />
  return <FileText className="w-4 h-4 text-yellow-400" />
}

export default function Quotes() {
  const [data, setData] = useState<PaginatedResponse<Quote> | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 20

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<Quote | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)
  const [downloadLoading, setDownloadLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [toast, setToast] = useState<Toast | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = useCallback((msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3500)
  }, [])

  const fetchQuotes = useCallback(async () => {
    setLoading(true)
    try {
      const result = await listQuotes({ page, per_page: perPage, status: statusFilter || undefined })
      setData(result)
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter])

  useEffect(() => { setPage(1) }, [statusFilter])
  useEffect(() => { fetchQuotes() }, [fetchQuotes])

  const openDetail = useCallback(async (id: number) => {
    setSelectedId(id)
    setDetail(null)
    setDetailLoading(true)
    try {
      const q = await getQuote(id)
      setDetail(q)
    } catch {
      showToast('Erro ao carregar orçamento', 'error')
      setSelectedId(null)
    } finally {
      setDetailLoading(false)
    }
  }, [showToast])

  const closeDetail = useCallback(() => {
    setSelectedId(null)
    setDetail(null)
  }, [])

  const handleGeneratePdf = useCallback(async () => {
    if (!detail) return
    setPdfLoading(true)
    try {
      const updated = await generatePdf(detail.id)
      setDetail(updated)
      setData((prev) => prev
        ? { ...prev, items: prev.items.map((q) => q.id === updated.id ? { ...q, pdf_url: updated.pdf_url } : q) }
        : prev
      )
      showToast('PDF gerado com sucesso!')
    } catch {
      showToast('Erro ao gerar PDF', 'error')
    } finally {
      setPdfLoading(false)
    }
  }, [detail, showToast])

  const handleDownloadPdf = useCallback(async () => {
    if (!detail) return
    setDownloadLoading(true)
    try {
      const code = detail.code || `ORC-${String(detail.id).padStart(4, '0')}`
      await downloadQuotePdf(detail.id, `orcamento-${code}.pdf`)
      showToast('Download iniciado!')
    } catch {
      showToast('Erro ao baixar PDF', 'error')
    } finally {
      setDownloadLoading(false)
    }
  }, [detail, showToast])

  const handleStatusChange = useCallback(async (nextStatus: Quote['status']) => {
    if (!detail) return
    setActionLoading(nextStatus)
    try {
      const updated = await updateQuote(detail.id, { status: nextStatus })
      setDetail(updated)
      setData((prev) => prev
        ? { ...prev, items: prev.items.map((q) => q.id === updated.id ? { ...q, status: updated.status } : q) }
        : prev
      )
      showToast(`Status atualizado para: ${STATUS_LABELS[nextStatus]}`)
    } catch {
      showToast('Erro ao atualizar status', 'error')
    } finally {
      setActionLoading(null)
    }
  }, [detail, showToast])

  const totalPages = data ? Math.ceil(data.total / perPage) : 0

  return (
    <div className="flex flex-col flex-1 overflow-hidden relative">
      <Topbar title="Orçamentos" subtitle={data ? `${data.total} registros` : ''} />

      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 transition-all ${
          toast.type === 'error' ? 'bg-red-700 text-white' : 'bg-emerald-700 text-white'
        }`}>
          {toast.type === 'error' ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      <main className="flex-1 overflow-hidden flex gap-0">
        <div className={`flex flex-col flex-1 overflow-hidden transition-all duration-300 ${selectedId ? 'mr-[420px]' : ''}`}>
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-6xl space-y-4">
              <div className="flex gap-2 overflow-x-auto pb-1">
                {STATUSES.map((s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === s
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
                            <th className="text-left text-slate-500 font-medium px-5 py-3">Código</th>
                            <th className="text-left text-slate-500 font-medium px-5 py-3">Cliente</th>
                            <th className="text-left text-slate-500 font-medium px-5 py-3">Status</th>
                            <th className="text-right text-slate-500 font-medium px-5 py-3">Total</th>
                            <th className="text-left text-slate-500 font-medium px-5 py-3 hidden md:table-cell">Data</th>
                            <th className="text-center text-slate-500 font-medium px-5 py-3">PDF</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-700">
                          {data.items.map((q) => (
                            <tr
                              key={q.id}
                              onClick={() => openDetail(q.id)}
                              className={`cursor-pointer transition-colors hover:bg-surface-700/50 ${
                                selectedId === q.id ? 'bg-brand-600/10 border-l-2 border-l-brand-500' : ''
                              }`}
                            >
                              <td className="px-5 py-3.5">
                                <div className="flex items-center gap-2">
                                  <StatusIcon status={q.status} />
                                  <div>
                                    <p className="text-white font-mono text-xs font-semibold">
                                      {q.code || `#${q.id}`}
                                    </p>
                                    {q.title && (
                                      <p className="text-slate-500 text-xs truncate max-w-32">{q.title}</p>
                                    )}
                                  </div>
                                </div>
                              </td>
                              <td className="px-5 py-3.5">
                                {q.client ? (
                                  <div>
                                    <p className="text-white text-sm font-medium">{q.client.name}</p>
                                    {q.client.phone && (
                                      <p className="text-slate-500 text-xs">{q.client.phone}</p>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-slate-600 text-xs">—</span>
                                )}
                              </td>
                              <td className="px-5 py-3.5"><Badge value={q.status} /></td>
                              <td className="px-5 py-3.5 text-right">
                                <span className="text-white font-semibold">{fmt(q.total_value)}</span>
                                {parseFloat(q.discount) > 0 && (
                                  <p className="text-red-400 text-xs">- {fmt(q.discount)}</p>
                                )}
                              </td>
                              <td className="px-5 py-3.5 hidden md:table-cell text-slate-400 text-xs">
                                {fmtDate(q.created_at)}
                              </td>
                              <td className="px-5 py-3.5 text-center">
                                {q.pdf_url ? (
                                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/20">
                                    <FileText className="w-3.5 h-3.5 text-emerald-400" />
                                  </span>
                                ) : (
                                  <span className="text-slate-700 text-xs">—</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {totalPages > 1 && (
                      <div className="flex items-center justify-between px-5 py-3 border-t border-surface-600">
                        <p className="text-slate-500 text-sm">
                          {(page - 1) * perPage + 1}–{Math.min(page * perPage, data.total)} de {data.total}
                        </p>
                        <div className="flex gap-2 items-center">
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
          </div>
        </div>

        {selectedId && (
          <div className="fixed right-0 top-0 h-full w-[420px] bg-surface-800 border-l border-surface-600 flex flex-col shadow-2xl z-40 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-600 shrink-0">
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="w-5 h-5 text-brand-400 shrink-0" />
                <div className="min-w-0">
                  <h2 className="text-white font-semibold text-sm truncate">
                    {detail?.code || `Orçamento #${selectedId}`}
                  </h2>
                  {detail && <p className="text-slate-500 text-xs">{fmtDate(detail.created_at)}</p>}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {detail && <Badge value={detail.status} />}
                <button onClick={closeDetail} className="btn-ghost p-1.5 rounded-lg">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {detailLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : detail ? (
              <div className="flex-1 overflow-y-auto">
                <div className="p-5 space-y-5">
                  <div className="bg-surface-700/50 rounded-xl p-4 space-y-3">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Cliente</p>
                    {detail.client ? (
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <User className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                          <span className="text-white text-sm font-medium">{detail.client.name}</span>
                        </div>
                        {detail.client.phone && (
                          <div className="flex items-center gap-2">
                            <Phone className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span className="text-slate-300 text-sm">{detail.client.phone}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-slate-500 text-sm">—</p>
                    )}
                    {detail.description && (
                      <p className="text-slate-400 text-xs leading-relaxed border-t border-surface-600 pt-2">{detail.description}</p>
                    )}
                  </div>

                  {detail.items && detail.items.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Itens</p>
                      <div className="rounded-xl overflow-hidden border border-surface-600">
                        <table className="w-full text-xs">
                          <thead className="bg-surface-700">
                            <tr>
                              <th className="text-left text-slate-400 font-medium px-3 py-2">Descrição</th>
                              <th className="text-right text-slate-400 font-medium px-3 py-2">Dim.</th>
                              <th className="text-right text-slate-400 font-medium px-3 py-2">Área</th>
                              <th className="text-right text-slate-400 font-medium px-3 py-2">Total</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-surface-700">
                            {detail.items.map((item) => (
                              <tr key={item.id} className="bg-surface-800">
                                <td className="px-3 py-2">
                                  <p className="text-white">{item.description}</p>
                                  {item.notes && (
                                    <p className="text-slate-500 text-[10px] mt-0.5">{item.notes}</p>
                                  )}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-300 whitespace-nowrap">
                                  {item.width_cm && item.height_cm
                                    ? `${dimM(item.width_cm)}×${dimM(item.height_cm)}`
                                    : '—'}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-300 whitespace-nowrap">
                                  {areaM2(item.width_cm, item.height_cm, item.quantity)}
                                </td>
                                <td className="px-3 py-2 text-right text-white font-semibold whitespace-nowrap">
                                  {fmt(item.total_price)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  <div className="bg-surface-700/50 rounded-xl p-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Subtotal</span>
                      <span className="text-white">{fmt(detail.subtotal)}</span>
                    </div>
                    {parseFloat(detail.discount) > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Desconto</span>
                        <span className="text-red-400">- {fmt(detail.discount)}</span>
                      </div>
                    )}
                    <div className="flex justify-between pt-2 border-t border-surface-600">
                      <span className="text-white font-semibold">Total</span>
                      <span className="text-emerald-400 font-bold text-base">{fmt(detail.total_value)}</span>
                    </div>
                  </div>

                  {detail.notes && (
                    <div className="bg-surface-700/30 rounded-xl p-4">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Observações</p>
                      <p className="text-slate-300 text-sm leading-relaxed">{detail.notes}</p>
                    </div>
                  )}
                </div>
              </div>
            ) : null}

            {detail && (
              <div className="shrink-0 border-t border-surface-600 p-4 space-y-3">
                <div className="flex gap-2">
                  <button
                    onClick={handleGeneratePdf}
                    disabled={pdfLoading || downloadLoading}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-surface-700 hover:bg-surface-600 text-slate-300 hover:text-white text-xs font-medium transition-colors disabled:opacity-50"
                  >
                    {pdfLoading ? (
                      <div className="w-3.5 h-3.5 border border-current border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <FilePlus2 className="w-3.5 h-3.5" />
                    )}
                    {detail.pdf_url ? 'Regen. PDF' : 'Gerar PDF'}
                  </button>
                  <button
                    onClick={handleDownloadPdf}
                    disabled={!detail.pdf_url || downloadLoading || pdfLoading}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {downloadLoading ? (
                      <div className="w-3.5 h-3.5 border border-current border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Download className="w-3.5 h-3.5" />
                    )}
                    Baixar PDF
                  </button>
                </div>

                {getStatusActions(detail.status).length > 0 && (
                  <div className="flex gap-2">
                    {getStatusActions(detail.status).map((action) => (
                      <button
                        key={action.nextStatus}
                        onClick={() => handleStatusChange(action.nextStatus)}
                        disabled={actionLoading !== null}
                        className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-white text-xs font-medium transition-colors disabled:opacity-50 ${action.color}`}
                      >
                        {actionLoading === action.nextStatus && (
                          <div className="w-3.5 h-3.5 border border-current border-t-transparent rounded-full animate-spin" />
                        )}
                        {action.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
