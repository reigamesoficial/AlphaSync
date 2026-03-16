import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Building2, Plus, Search, X, CheckCircle2, XCircle, Settings2,
  ShieldCheck, Users, ChevronLeft, ChevronRight, AlertCircle,
  ToggleLeft, ToggleRight, UserPlus, RefreshCw,
} from 'lucide-react'
import {
  listCompanies, getCompany, createCompany, updateCompany, bootstrapAdmin,
  type CompanyListItem, type CompanyDetail, type CreateCompanyPayload,
} from '../../api/admin'
import type { PaginatedResponse } from '../../types'

const DOMAIN_LABELS: Record<string, string> = {
  protection_network: 'Redes de Proteção',
  hvac: 'Climatização (HVAC)',
  electrician: 'Elétrica',
  plumbing: 'Hidráulica',
  cleaning: 'Limpeza',
  glass_installation: 'Vidraçaria',
  pest_control: 'Dedetização',
  security_cameras: 'Câmeras de Seg.',
}

const DOMAIN_ICONS: Record<string, string> = {
  protection_network: '🕸️', hvac: '❄️', electrician: '⚡',
  plumbing: '🔧', cleaning: '🧹', glass_installation: '🪟',
  pest_control: '🐛', security_cameras: '📷',
}

const PLAN_OPTIONS = ['starter', 'pro', 'enterprise']

function slugify(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR')
}

interface Toast { msg: string; type: 'success' | 'error' }

function Toast({ toast }: { toast: Toast }) {
  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl text-sm font-medium backdrop-blur border ${
      toast.type === 'error'
        ? 'bg-red-500/20 text-red-300 border-red-500/30'
        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
    }`}>
      {toast.type === 'error' ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
      {toast.msg}
    </div>
  )
}

function StatCard({ label, value, color, icon: Icon }: { label: string; value: number; color: string; icon: React.ElementType }) {
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between mb-2">
        <span className="text-slate-400 text-xs font-medium">{label}</span>
        <Icon className={`w-4 h-4 ${color} opacity-60`} />
      </div>
      <span className={`text-2xl font-bold ${color}`}>{value}</span>
    </div>
  )
}

function ConfigBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
      ok ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'
    }`}>
      {ok ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      {label}
    </span>
  )
}

function StatusPill({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
      active ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-500/15 text-slate-400'
    }`}>
      {active ? <ToggleRight className="w-3 h-3" /> : <ToggleLeft className="w-3 h-3" />}
      {active ? 'Ativa' : 'Inativa'}
    </span>
  )
}

const EMPTY_CREATE: CreateCompanyPayload = {
  name: '', slug: '', service_domain: 'protection_network', plan_name: '',
  admin_name: '', admin_email: '', admin_password: '',
}

export default function AdminCompanies() {
  const [data, setData] = useState<PaginatedResponse<CompanyListItem> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 20

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<CompanyDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState<CreateCompanyPayload>(EMPTY_CREATE)
  const [slugEdited, setSlugEdited] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  const [bootstrapOpen, setBootstrapOpen] = useState(false)
  const [bsForm, setBsForm] = useState({ admin_name: '', admin_email: '', admin_password: '' })
  const [bsLoading, setBsLoading] = useState(false)
  const [bsError, setBsError] = useState('')

  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = useCallback((msg: string, type: Toast['type'] = 'success') => {
    setToast({ msg, type })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3500)
  }, [])

  const fetchList = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listCompanies({ page, per_page: perPage, search: search || undefined })
      setData(res)
    } catch { setData(null) } finally { setLoading(false) }
  }, [page, search])

  useEffect(() => { setPage(1) }, [search])
  useEffect(() => { fetchList() }, [fetchList])

  const openDetail = useCallback(async (id: number) => {
    setSelectedId(id)
    setDetail(null)
    setDetailLoading(true)
    setBootstrapOpen(false)
    setBsError('')
    try { setDetail(await getCompany(id)) }
    catch { showToast('Erro ao carregar empresa', 'error'); setSelectedId(null) }
    finally { setDetailLoading(false) }
  }, [showToast])

  const closeDetail = () => { setSelectedId(null); setDetail(null); setBootstrapOpen(false) }

  const handleToggleActive = async () => {
    if (!detail) return
    setActionLoading(true)
    try {
      const updated = await updateCompany(detail.id, { is_active: !detail.is_active })
      setDetail(updated)
      setData(prev => prev ? {
        ...prev,
        items: prev.items.map(c => c.id === updated.id ? { ...c, is_active: updated.is_active } : c)
      } : prev)
      showToast(`Empresa ${updated.is_active ? 'ativada' : 'desativada'}!`)
    } catch { showToast('Erro ao alterar status', 'error') }
    finally { setActionLoading(false) }
  }

  const handlePlanSave = async (planName: string) => {
    if (!detail) return
    try {
      const updated = await updateCompany(detail.id, { plan_name: planName || undefined })
      setDetail(updated)
      setData(prev => prev ? {
        ...prev,
        items: prev.items.map(c => c.id === updated.id ? { ...c, plan_name: updated.plan_name } : c)
      } : prev)
      showToast('Plano atualizado!')
    } catch { showToast('Erro ao atualizar plano', 'error') }
  }

  const handleBootstrapAdmin = async () => {
    if (!detail) return
    setBsLoading(true)
    setBsError('')
    try {
      const updated = await bootstrapAdmin(detail.id, {
        admin_name: bsForm.admin_name,
        admin_email: bsForm.admin_email,
        admin_password: bsForm.admin_password,
      })
      setDetail(updated)
      setData(prev => prev ? {
        ...prev,
        items: prev.items.map(c => c.id === updated.id ? { ...c, has_admin: updated.has_admin } : c)
      } : prev)
      setBootstrapOpen(false)
      setBsForm({ admin_name: '', admin_email: '', admin_password: '' })
      showToast('Admin criado com sucesso!')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setBsError(msg || 'Erro ao criar admin.')
    } finally { setBsLoading(false) }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setCreateError('')
    try {
      const payload = { ...form }
      if (!payload.plan_name) delete payload.plan_name
      if (!payload.whatsapp_phone_number_id) delete payload.whatsapp_phone_number_id
      if (!payload.support_email) delete payload.support_email
      const created = await createCompany(payload)
      setCreateOpen(false)
      setForm(EMPTY_CREATE)
      setSlugEdited(false)
      showToast(`Empresa "${created.name}" criada com sucesso!`)
      fetchList()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCreateError(msg || 'Erro ao criar empresa.')
    } finally { setCreating(false) }
  }

  const handleNameChange = (v: string) => {
    setForm(f => ({ ...f, name: v, slug: slugEdited ? f.slug : slugify(v) }))
  }

  const totalPages = data ? Math.ceil(data.total / perPage) : 0

  const stats = data ? {
    total: data.total,
    active: data.items.filter(c => c.is_active).length,
    noAdmin: data.items.filter(c => !c.has_admin).length,
    noSettings: data.items.filter(c => !c.has_settings).length,
  } : null

  return (
    <div className="flex flex-col flex-1 overflow-hidden relative">
      {toast && <Toast toast={toast} />}

      <main className="flex-1 overflow-hidden flex">
        {/* Main content */}
        <div className={`flex flex-col flex-1 overflow-hidden transition-all duration-300 ${selectedId ? 'mr-[460px]' : ''}`}>

          {/* Sticky header */}
          <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur border-b border-surface-700 px-6 py-4 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-violet-600/20 rounded-lg flex items-center justify-center">
                <Building2 className="w-4 h-4 text-violet-400" />
              </div>
              <div>
                <h1 className="text-white font-semibold text-base">Empresas</h1>
                <p className="text-slate-500 text-xs">{data?.total ?? '…'} empresa{data?.total !== 1 ? 's' : ''} cadastrada{data?.total !== 1 ? 's' : ''}</p>
              </div>
            </div>
            <button
              onClick={() => { setCreateOpen(true); setCreateError(''); setForm(EMPTY_CREATE); setSlugEdited(false) }}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" />
              Nova Empresa
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {/* Stat cards */}
            {stats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="Total" value={stats.total} color="text-violet-400" icon={Building2} />
                <StatCard label="Ativas (pág.)" value={stats.active} color="text-emerald-400" icon={CheckCircle2} />
                <StatCard label="Sem admin" value={stats.noAdmin} color="text-amber-400" icon={AlertCircle} />
                <StatCard label="Sem config" value={stats.noSettings} color="text-red-400" icon={Settings2} />
              </div>
            )}

            {/* Search bar */}
            <div className="flex gap-2">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  className="input pl-9"
                  placeholder="Buscar empresa, slug..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <button onClick={fetchList} className="btn-secondary px-3">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            {/* Table */}
            <div className="card overflow-hidden">
              {loading ? (
                <div className="flex items-center justify-center h-40">
                  <div className="w-7 h-7 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : !data || data.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-12 gap-3">
                  <div className="w-12 h-12 bg-surface-700 rounded-xl flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-slate-600" />
                  </div>
                  <p className="text-slate-400 text-sm">Nenhuma empresa encontrada.</p>
                  {search && <button onClick={() => setSearch('')} className="text-xs text-violet-400 hover:text-violet-300">Limpar filtro</button>}
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-surface-600 bg-surface-900/50">
                          <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium">Empresa</th>
                          <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium hidden md:table-cell">Domínio</th>
                          <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium hidden lg:table-cell">Plano</th>
                          <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium">Status</th>
                          <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium hidden xl:table-cell">Config</th>
                          <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium hidden xl:table-cell">Usuários</th>
                          <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium hidden lg:table-cell">Criada</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-surface-700">
                        {data.items.map(c => (
                          <tr
                            key={c.id}
                            onClick={() => openDetail(c.id)}
                            className={`cursor-pointer transition-colors hover:bg-surface-700/40 ${
                              selectedId === c.id ? 'bg-violet-600/10 border-l-2 border-l-violet-500' : ''
                            }`}
                          >
                            <td className="px-5 py-3.5">
                              <div className="flex items-center gap-2.5">
                                <span className="text-lg leading-none">{DOMAIN_ICONS[c.service_domain] ?? '🏢'}</span>
                                <div>
                                  <p className="text-white font-semibold">{c.name}</p>
                                  <p className="text-slate-500 text-xs font-mono">{c.slug}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-5 py-3.5 hidden md:table-cell">
                              <span className="text-slate-300 text-xs">{DOMAIN_LABELS[c.service_domain] ?? c.service_domain}</span>
                            </td>
                            <td className="px-5 py-3.5 hidden lg:table-cell">
                              {c.plan_name ? (
                                <span className="inline-flex text-xs font-medium px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400">{c.plan_name}</span>
                              ) : (
                                <span className="text-slate-600 text-xs">—</span>
                              )}
                            </td>
                            <td className="px-5 py-3.5"><StatusPill active={c.is_active} /></td>
                            <td className="px-5 py-3.5 hidden xl:table-cell">
                              <div className="flex gap-1 flex-wrap">
                                <ConfigBadge ok={c.has_settings} label="Config" />
                                <ConfigBadge ok={c.has_admin} label="Admin" />
                              </div>
                            </td>
                            <td className="px-5 py-3.5 hidden xl:table-cell">
                              <span className="flex items-center gap-1 text-slate-400 text-xs">
                                <Users className="w-3 h-3" /> {c.user_count}
                              </span>
                            </td>
                            <td className="px-5 py-3.5 hidden lg:table-cell text-slate-500 text-xs">{fmtDate(c.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {totalPages > 1 && (
                    <div className="flex items-center justify-between px-5 py-3 border-t border-surface-600 bg-surface-900/30">
                      <p className="text-slate-500 text-xs">{(page-1)*perPage+1}–{Math.min(page*perPage, data.total)} de {data.total}</p>
                      <div className="flex gap-2 items-center">
                        <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} className="btn-ghost p-1.5 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
                        <span className="text-slate-400 text-sm">{page} / {totalPages}</span>
                        <button onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page === totalPages} className="btn-ghost p-1.5 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Detail panel */}
        {selectedId && (
          <div className="fixed right-0 top-0 h-full w-[460px] bg-surface-800 border-l border-surface-600 flex flex-col shadow-2xl z-40 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-600 shrink-0">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 bg-violet-600/15 border border-violet-500/25 rounded-xl flex items-center justify-center text-xl shrink-0">
                  {detail ? (DOMAIN_ICONS[detail.service_domain] ?? '🏢') : '🏢'}
                </div>
                <div className="min-w-0">
                  <h2 className="text-white font-semibold text-sm truncate">{detail?.name ?? '…'}</h2>
                  {detail && <p className="text-slate-500 text-xs font-mono">{detail.slug} · #{detail.id}</p>}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {detail && <StatusPill active={detail.is_active} />}
                <button onClick={closeDetail} className="text-slate-400 hover:text-white transition-colors p-1"><X className="w-4 h-4" /></button>
              </div>
            </div>

            {detailLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : detail ? (
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {/* Info grid */}
                <div className="card divide-y divide-surface-600">
                  {[
                    { label: 'Domínio', value: DOMAIN_LABELS[detail.service_domain] ?? detail.service_domain },
                    { label: 'Usuários', value: String(detail.user_count) },
                    { label: 'Criada em', value: fmtDate(detail.created_at) },
                    { label: 'Atualizada', value: fmtDate(detail.updated_at) },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex justify-between items-center px-4 py-3 text-xs">
                      <span className="text-slate-500">{label}</span>
                      <span className="text-slate-300 font-medium">{value}</span>
                    </div>
                  ))}
                  <div className="flex justify-between items-center px-4 py-3 text-xs">
                    <span className="text-slate-500">Plano</span>
                    <select
                      className="bg-transparent text-slate-300 text-xs font-medium focus:outline-none cursor-pointer"
                      value={detail.plan_name ?? ''}
                      onChange={e => handlePlanSave(e.target.value)}
                    >
                      <option value="">— Sem plano —</option>
                      {PLAN_OPTIONS.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                </div>

                {/* Config status */}
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Status de configuração</p>
                  <div className="flex flex-wrap gap-2">
                    <ConfigBadge ok={detail.has_settings} label="Settings criadas" />
                    <ConfigBadge ok={detail.has_admin} label="Admin configurado" />
                    {detail.settings?.bot_name && (
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400">
                        Bot: {detail.settings.bot_name}
                      </span>
                    )}
                    {detail.settings?.quote_prefix && (
                      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-slate-500/15 text-slate-400">
                        Prefix: {detail.settings.quote_prefix}
                      </span>
                    )}
                  </div>
                </div>

                {/* Admins */}
                {detail.admin_users.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Admins da empresa</p>
                    <div className="space-y-2">
                      {detail.admin_users.map(u => (
                        <div key={u.id} className="flex items-center gap-3 card px-4 py-3">
                          <div className="w-7 h-7 rounded-full bg-violet-600/20 flex items-center justify-center text-xs font-bold text-violet-400 shrink-0">
                            {u.name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-white text-xs font-medium truncate">{u.name}</p>
                            <p className="text-slate-500 text-xs truncate">{u.email}</p>
                          </div>
                          <span className={`text-xs ${u.is_active ? 'text-emerald-400' : 'text-slate-500'}`}>
                            {u.is_active ? 'Ativo' : 'Inativo'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Extra settings */}
                {detail.settings?.extra_settings && Object.keys(detail.settings.extra_settings).length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Configurações de domínio</p>
                    <div className="card divide-y divide-surface-600">
                      {Object.entries(detail.settings.extra_settings).map(([k, v]) => (
                        <div key={k} className="flex justify-between items-center px-4 py-2.5 text-xs">
                          <span className="text-slate-400 font-mono">{k}</span>
                          <span className="text-slate-300 truncate max-w-36 text-right">
                            {typeof v === 'object' ? JSON.stringify(v).slice(0, 40) : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Bootstrap admin form */}
                {bootstrapOpen && (
                  <div className="card p-4 space-y-3 border-violet-500/30">
                    <p className="text-white text-sm font-semibold flex items-center gap-2">
                      <UserPlus className="w-4 h-4 text-violet-400" /> Criar Admin Inicial
                    </p>
                    {bsError && (
                      <div className="bg-red-500/15 border border-red-500/30 rounded-lg px-3 py-2 text-red-400 text-xs">{bsError}</div>
                    )}
                    {['admin_name', 'admin_email', 'admin_password'].map(field => (
                      <input
                        key={field}
                        type={field === 'admin_password' ? 'password' : 'text'}
                        placeholder={{ admin_name: 'Nome do admin', admin_email: 'E-mail', admin_password: 'Senha (mín. 6 chars)' }[field]}
                        value={bsForm[field as keyof typeof bsForm]}
                        onChange={e => setBsForm(f => ({ ...f, [field]: e.target.value }))}
                        className="input"
                      />
                    ))}
                    <div className="flex gap-2">
                      <button onClick={() => setBootstrapOpen(false)} className="flex-1 btn-secondary text-sm">Cancelar</button>
                      <button
                        onClick={handleBootstrapAdmin}
                        disabled={bsLoading}
                        className="flex-1 btn-primary text-sm flex items-center justify-center gap-2"
                      >
                        {bsLoading && <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin" />}
                        {bsLoading ? 'Criando…' : 'Criar Admin'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            {/* Footer actions */}
            {detail && (
              <div className="shrink-0 border-t border-surface-600 p-4 space-y-2">
                {!detail.has_admin && !bootstrapOpen && (
                  <button
                    onClick={() => setBootstrapOpen(true)}
                    className="w-full btn-primary flex items-center justify-center gap-2 text-sm"
                  >
                    <UserPlus className="w-4 h-4" />
                    Criar Admin Inicial
                  </button>
                )}
                <button
                  onClick={handleToggleActive}
                  disabled={actionLoading}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors border disabled:opacity-50 ${
                    detail.is_active
                      ? 'bg-transparent border-surface-500 text-slate-400 hover:text-red-400 hover:border-red-500/40'
                      : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25'
                  }`}
                >
                  {actionLoading
                    ? <div className="w-4 h-4 border border-current border-t-transparent rounded-full animate-spin" />
                    : detail.is_active ? <ToggleLeft className="w-4 h-4" /> : <ToggleRight className="w-4 h-4" />
                  }
                  {detail.is_active ? 'Desativar empresa' : 'Ativar empresa'}
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Create modal */}
      {createOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-800 rounded-2xl border border-surface-600 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-surface-600">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-violet-600/20 rounded-lg flex items-center justify-center">
                  <Building2 className="w-4 h-4 text-violet-400" />
                </div>
                <h2 className="text-white font-semibold">Nova Empresa</h2>
              </div>
              <button onClick={() => setCreateOpen(false)} className="text-slate-400 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4 overflow-y-auto max-h-[80vh]">
              {createError && (
                <div className="bg-red-500/15 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />{createError}
                </div>
              )}

              <div className="space-y-1">
                <p className="text-slate-500 text-xs font-semibold uppercase tracking-widest">Dados da empresa</p>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="label">Nome da empresa *</label>
                  <input required value={form.name} onChange={e => handleNameChange(e.target.value)} className="input" placeholder="Ex: Redes Silva & Cia" />
                </div>
                <div>
                  <label className="label">Slug (identificador único) *</label>
                  <input required value={form.slug}
                    onChange={e => { setSlugEdited(true); setForm(f => ({ ...f, slug: e.target.value })) }}
                    className="input font-mono" placeholder="redes-silva" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label">Domínio</label>
                    <select value={form.service_domain} onChange={e => setForm(f => ({ ...f, service_domain: e.target.value }))} className="input">
                      {Object.entries(DOMAIN_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="label">Plano</label>
                    <select value={form.plan_name ?? ''} onChange={e => setForm(f => ({ ...f, plan_name: e.target.value }))} className="input">
                      <option value="">— Sem plano —</option>
                      {PLAN_OPTIONS.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="label">WhatsApp Phone Number ID</label>
                  <input value={form.whatsapp_phone_number_id ?? ''} onChange={e => setForm(f => ({ ...f, whatsapp_phone_number_id: e.target.value }))}
                    className="input font-mono" placeholder="Opcional — ID do número WhatsApp Business" />
                </div>
              </div>

              <div className="border-t border-surface-600 pt-4 space-y-3">
                <p className="text-slate-500 text-xs font-semibold uppercase tracking-widest">Admin inicial</p>
                <div>
                  <label className="label">Nome do admin *</label>
                  <input required value={form.admin_name} onChange={e => setForm(f => ({ ...f, admin_name: e.target.value }))} className="input" placeholder="João Silva" />
                </div>
                <div>
                  <label className="label">E-mail do admin *</label>
                  <input required type="email" value={form.admin_email} onChange={e => setForm(f => ({ ...f, admin_email: e.target.value }))} className="input" placeholder="joao@empresa.com" />
                </div>
                <div>
                  <label className="label">Senha *</label>
                  <input required type="password" minLength={6} value={form.admin_password} onChange={e => setForm(f => ({ ...f, admin_password: e.target.value }))} className="input" placeholder="••••••••" />
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setCreateOpen(false)} className="flex-1 btn-secondary text-sm">Cancelar</button>
                <button type="submit" disabled={creating} className="flex-1 btn-primary text-sm flex items-center justify-center gap-2">
                  {creating && <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin" />}
                  {creating ? 'Criando…' : 'Criar Empresa'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
