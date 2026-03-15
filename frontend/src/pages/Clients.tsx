import { useEffect, useState, useCallback } from 'react'
import { Users, Search, Plus, Phone, Mail, ChevronLeft, ChevronRight } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import { PageSpinner } from '../components/ui/Spinner'
import { listClients } from '../api/clients'
import type { Client, PaginatedResponse } from '../types'

const STATUSES = ['', 'lead', 'qualified', 'customer', 'inactive']
const STATUS_LABELS: Record<string, string> = {
  '': 'Todos', lead: 'Lead', qualified: 'Qualificado', customer: 'Cliente', inactive: 'Inativo',
}

function formatPhone(phone: string) {
  const d = phone.replace(/\D/g, '')
  if (d.length === 13) return `+${d.slice(0,2)} (${d.slice(2,4)}) ${d.slice(4,9)}-${d.slice(9)}`
  if (d.length === 11) return `(${d.slice(0,2)}) ${d.slice(2,7)}-${d.slice(7)}`
  return phone
}

export default function Clients() {
  const [data, setData] = useState<PaginatedResponse<Client> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 20

  const fetchClients = useCallback(async () => {
    setLoading(true)
    try {
      const result = await listClients({
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
  useEffect(() => { fetchClients() }, [fetchClients])

  const totalPages = data ? Math.ceil(data.total / perPage) : 0

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title="Clientes" subtitle={data ? `${data.total} registros` : ''} />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                className="input pl-9"
                placeholder="Buscar por nome, telefone ou e-mail..."
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
            <button className="btn-primary flex items-center gap-2 shrink-0">
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">Novo cliente</span>
            </button>
          </div>

          <div className="card overflow-hidden">
            {loading ? (
              <PageSpinner />
            ) : !data || data.items.length === 0 ? (
              <EmptyState
                icon={<Users className="w-10 h-10" />}
                title="Nenhum cliente encontrado"
                description="Ajuste os filtros ou cadastre um novo cliente."
              />
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-surface-600">
                        <th className="text-left text-slate-500 font-medium px-5 py-3">Nome</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden md:table-cell">Telefone</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden lg:table-cell">E-mail</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3">Status</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden lg:table-cell">Origem</th>
                        <th className="text-left text-slate-500 font-medium px-5 py-3 hidden xl:table-cell">Cadastro</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-700">
                      {data.items.map((c) => (
                        <tr key={c.id} className="hover:bg-surface-700/30 transition-colors">
                          <td className="px-5 py-3.5">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-brand-600/20 flex items-center justify-center shrink-0">
                                <span className="text-brand-400 text-xs font-semibold">
                                  {c.name.charAt(0).toUpperCase()}
                                </span>
                              </div>
                              <div className="min-w-0">
                                <p className="text-white font-medium truncate">{c.name}</p>
                                <p className="text-slate-500 text-xs md:hidden">{formatPhone(c.phone)}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-3.5 hidden md:table-cell">
                            <span className="flex items-center gap-1.5 text-slate-300">
                              <Phone className="w-3.5 h-3.5 text-slate-500" />
                              {formatPhone(c.phone)}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 hidden lg:table-cell">
                            {c.email ? (
                              <span className="flex items-center gap-1.5 text-slate-300">
                                <Mail className="w-3.5 h-3.5 text-slate-500" />
                                {c.email}
                              </span>
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                          <td className="px-5 py-3.5">
                            <Badge value={c.status} />
                          </td>
                          <td className="px-5 py-3.5 hidden lg:table-cell">
                            <Badge value={c.lead_source} />
                          </td>
                          <td className="px-5 py-3.5 hidden xl:table-cell text-slate-400 text-xs">
                            {new Date(c.created_at).toLocaleDateString('pt-BR')}
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
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="btn-ghost p-1.5 disabled:opacity-40"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <span className="text-slate-400 text-sm px-2 py-1.5">{page} / {totalPages}</span>
                      <button
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="btn-ghost p-1.5 disabled:opacity-40"
                      >
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
