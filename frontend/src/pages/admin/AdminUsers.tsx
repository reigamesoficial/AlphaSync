import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Users, Plus, Search, X, CheckCircle2, XCircle,
  ShieldCheck, Building2, ChevronLeft, ChevronRight,
  ToggleLeft, ToggleRight, RefreshCw, Eye, EyeOff,
} from 'lucide-react'
import {
  listUsers, getUser, createUser, updateUser, listCompanies,
  type AdminUser, type CreateUserPayload, type UpdateUserPayload,
  type CompanyListItem,
} from '../../api/admin'
import type { PaginatedResponse } from '../../types'

const ROLE_LABELS: Record<string, string> = {
  master_admin: 'Master Admin',
  company_admin: 'Administrador',
  seller: 'Vendedor',
  installer: 'Instalador',
  viewer: 'Visualizador',
}

const ROLE_COLORS: Record<string, string> = {
  master_admin: 'bg-violet-500/20 text-violet-400',
  company_admin: 'bg-blue-500/20 text-blue-400',
  seller: 'bg-emerald-500/20 text-emerald-400',
  installer: 'bg-amber-500/20 text-amber-400',
  viewer: 'bg-slate-500/20 text-slate-400',
}

const ALL_ROLES = ['master_admin', 'company_admin', 'seller', 'installer', 'viewer']

function fmtDate(iso: string) { return new Date(iso).toLocaleDateString('pt-BR') }

interface Toast { msg: string; type: 'success' | 'error' }

const EMPTY_CREATE: CreateUserPayload = {
  name: '', email: '', password: '', role: 'company_admin', company_id: null, is_active: true,
}

const INPUT = "w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
const SELECT = "w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-violet-500"

function RoleBadge({ role }: { role: string }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${ROLE_COLORS[role] ?? 'bg-slate-500/20 text-slate-400'}`}>
      {ROLE_LABELS[role] ?? role}
    </span>
  )
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
      active ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-500/15 text-slate-400'
    }`}>
      {active ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

export default function AdminUsers() {
  const [data, setData] = useState<PaginatedResponse<AdminUser> | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [companyFilter, setCompanyFilter] = useState<number | ''>('')
  const [page, setPage] = useState(1)
  const perPage = 20

  const [companies, setCompanies] = useState<CompanyListItem[]>([])

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<AdminUser | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const [editForm, setEditForm] = useState<UpdateUserPayload>({})
  const [editDirty, setEditDirty] = useState(false)
  const [editSaving, setEditSaving] = useState(false)
  const [editError, setEditError] = useState('')
  const [showPwSection, setShowPwSection] = useState(false)
  const [newPw, setNewPw] = useState('')
  const [showPw, setShowPw] = useState(false)

  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<CreateUserPayload>(EMPTY_CREATE)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const [showCreatePw, setShowCreatePw] = useState(false)

  const [toast, setToast] = useState<Toast | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const showToast = useCallback((msg: string, type: Toast['type'] = 'success') => {
    setToast({ msg, type })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3500)
  }, [])

  useEffect(() => {
    listCompanies({ per_page: 200 }).then(r => setCompanies(r.items)).catch(() => {})
  }, [])

  const fetchList = useCallback(async () => {
    setLoading(true)
    try {
      const params: Parameters<typeof listUsers>[0] = { page, per_page: perPage }
      if (search) params.search = search
      if (roleFilter) params.role = roleFilter
      if (companyFilter !== '') params.company_id = Number(companyFilter)
      setData(await listUsers(params))
    } catch { setData(null) } finally { setLoading(false) }
  }, [page, search, roleFilter, companyFilter])

  useEffect(() => { setPage(1) }, [search, roleFilter, companyFilter])
  useEffect(() => { fetchList() }, [fetchList])

  const openDetail = useCallback(async (id: number) => {
    setSelectedId(id)
    setDetail(null)
    setDetailLoading(true)
    setEditError('')
    setShowPwSection(false)
    setNewPw('')
    try {
      const u = await getUser(id)
      setDetail(u)
      setEditForm({
        name: u.name, email: u.email, role: u.role,
        company_id: u.company_id, is_active: u.is_active,
      })
      setEditDirty(false)
    } catch { showToast('Erro ao carregar usuário', 'error'); setSelectedId(null) }
    finally { setDetailLoading(false) }
  }, [showToast])

  const closeDetail = () => { setSelectedId(null); setDetail(null); setEditDirty(false) }

  function setEdit(k: keyof UpdateUserPayload, v: unknown) {
    setEditForm(f => ({ ...f, [k]: v }))
    setEditDirty(true)
    setEditError('')
  }

  const handleSaveEdit = async () => {
    if (!detail) return
    setEditSaving(true)
    setEditError('')
    try {
      const payload = { ...editForm }
      if (showPwSection && newPw) payload.password = newPw
      const updated = await updateUser(detail.id, payload)
      setDetail(updated)
      setEditDirty(false)
      setShowPwSection(false)
      setNewPw('')
      setData(prev => prev ? { ...prev, items: prev.items.map(u => u.id === updated.id ? { ...u, ...updated } : u) } : prev)
      showToast('Usuário atualizado!')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setEditError(msg || 'Erro ao salvar.')
    } finally { setEditSaving(false) }
  }

  const handleToggleActive = async () => {
    if (!detail) return
    setActionLoading(true)
    try {
      const updated = await updateUser(detail.id, { is_active: !detail.is_active })
      setDetail(updated)
      setData(prev => prev ? { ...prev, items: prev.items.map(u => u.id === updated.id ? { ...u, is_active: updated.is_active } : u) } : prev)
      showToast(`Usuário ${updated.is_active ? 'ativado' : 'desativado'}!`)
    } catch { showToast('Erro ao alterar status', 'error') }
    finally { setActionLoading(false) }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setCreateError('')
    try {
      const payload = { ...createForm }
      if (payload.role === 'master_admin') payload.company_id = null
      const created = await createUser(payload)
      setCreateOpen(false)
      setCreateForm(EMPTY_CREATE)
      showToast(`Usuário "${created.name}" criado!`)
      fetchList()
      openDetail(created.id)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCreateError(msg || 'Erro ao criar usuário.')
    } finally { setCreating(false) }
  }

  const totalPages = data ? Math.ceil(data.total / perPage) : 0
  const isMasterRole = (r: string) => r === 'master_admin'

  return (
    <div className="flex flex-col flex-1 overflow-hidden relative">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 ${
          toast.type === 'error' ? 'bg-red-700 text-white' : 'bg-emerald-700 text-white'
        }`}>
          {toast.type === 'error' ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      <main className="flex-1 overflow-hidden flex">
        <div className={`flex flex-col flex-1 overflow-hidden transition-all duration-300 ${selectedId ? 'mr-[440px]' : ''}`}>
          <div className="flex-1 overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-xl font-bold text-white">Usuários</h1>
                <p className="text-slate-400 text-sm mt-0.5">{data?.total ?? '…'} usuário{data?.total !== 1 ? 's' : ''} cadastrado{data?.total !== 1 ? 's' : ''}</p>
              </div>
              <button
                onClick={() => { setCreateOpen(true); setCreateError(''); setCreateForm(EMPTY_CREATE) }}
                className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                Novo Usuário
              </button>
            </div>

            <div className="flex flex-wrap gap-2 mb-4">
              <div className="relative flex-1 min-w-48">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  className="w-full bg-surface-700 border border-surface-600 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
                  placeholder="Buscar por nome ou e-mail..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <select
                className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-violet-500"
                value={roleFilter}
                onChange={e => setRoleFilter(e.target.value)}
              >
                <option value="">Todos os papéis</option>
                {ALL_ROLES.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
              </select>
              <select
                className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-violet-500"
                value={companyFilter}
                onChange={e => setCompanyFilter(e.target.value === '' ? '' : Number(e.target.value))}
              >
                <option value="">Todas as empresas</option>
                <option value="0">Sem empresa (Master)</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <button onClick={fetchList} className="btn-ghost p-2 rounded-lg">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            <div className="card overflow-hidden">
              {loading ? (
                <div className="flex items-center justify-center h-40">
                  <div className="w-7 h-7 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : !data || data.items.length === 0 ? (
                <div className="p-10 text-center">
                  <Users className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm">Nenhum usuário encontrado.</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-surface-600">
                          <th className="text-left px-5 py-3 text-slate-500 font-medium">Usuário</th>
                          <th className="text-left px-5 py-3 text-slate-500 font-medium">Papel</th>
                          <th className="text-left px-5 py-3 text-slate-500 font-medium hidden md:table-cell">Empresa</th>
                          <th className="text-left px-5 py-3 text-slate-500 font-medium">Status</th>
                          <th className="text-left px-5 py-3 text-slate-500 font-medium hidden lg:table-cell">Criado</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-surface-700">
                        {data.items.map(u => (
                          <tr
                            key={u.id}
                            onClick={() => openDetail(u.id)}
                            className={`cursor-pointer transition-colors hover:bg-surface-700/50 ${
                              selectedId === u.id ? 'bg-violet-600/10 border-l-2 border-l-violet-500' : ''
                            }`}
                          >
                            <td className="px-5 py-3.5">
                              <p className="text-white font-semibold">{u.name}</p>
                              <p className="text-slate-500 text-xs">{u.email}</p>
                            </td>
                            <td className="px-5 py-3.5"><RoleBadge role={u.role} /></td>
                            <td className="px-5 py-3.5 hidden md:table-cell">
                              {u.company_name ? (
                                <span className="flex items-center gap-1.5 text-slate-300 text-xs">
                                  <Building2 className="w-3 h-3 text-slate-500" />
                                  {u.company_name}
                                </span>
                              ) : (
                                <span className="flex items-center gap-1.5 text-slate-600 text-xs">
                                  <ShieldCheck className="w-3 h-3" />
                                  Master
                                </span>
                              )}
                            </td>
                            <td className="px-5 py-3.5"><StatusBadge active={u.is_active} /></td>
                            <td className="px-5 py-3.5 hidden lg:table-cell text-slate-500 text-xs">{fmtDate(u.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {totalPages > 1 && (
                    <div className="flex items-center justify-between px-5 py-3 border-t border-surface-600">
                      <p className="text-slate-500 text-sm">{(page-1)*perPage+1}–{Math.min(page*perPage, data.total)} de {data.total}</p>
                      <div className="flex gap-2 items-center">
                        <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page===1} className="btn-ghost p-1.5 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
                        <span className="text-slate-400 text-sm">{page} / {totalPages}</span>
                        <button onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page===totalPages} className="btn-ghost p-1.5 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        {selectedId && (
          <div className="fixed right-0 top-0 h-full w-[440px] bg-surface-800 border-l border-surface-600 flex flex-col shadow-2xl z-40 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-600 shrink-0">
              <div className="flex items-center gap-3 min-w-0">
                <Users className="w-5 h-5 text-violet-400 shrink-0" />
                <div className="min-w-0">
                  <h2 className="text-white font-semibold text-sm truncate">{detail?.name ?? '...'}</h2>
                  {detail && <p className="text-slate-500 text-xs">ID {detail.id} · {detail.email}</p>}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {detail && <RoleBadge role={detail.role} />}
                <button onClick={closeDetail} className="btn-ghost p-1.5 rounded-lg"><X className="w-4 h-4" /></button>
              </div>
            </div>

            {detailLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : detail ? (
              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {editError && (
                  <div className="bg-red-500/15 border border-red-500/30 rounded-lg px-3 py-2 text-red-400 text-xs">{editError}</div>
                )}

                <div>
                  <label className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2 block">Nome</label>
                  <input className={INPUT} value={editForm.name ?? ''} onChange={e => setEdit('name', e.target.value)} />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2 block">E-mail</label>
                  <input className={INPUT} type="email" value={editForm.email ?? ''} onChange={e => setEdit('email', e.target.value)} />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2 block">Papel</label>
                  <select
                    className={SELECT}
                    value={editForm.role ?? ''}
                    onChange={e => {
                      setEdit('role', e.target.value)
                      if (e.target.value === 'master_admin') setEdit('company_id', null)
                    }}
                  >
                    {ALL_ROLES.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                  </select>
                </div>
                {editForm.role !== 'master_admin' && (
                  <div>
                    <label className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2 block">Empresa</label>
                    <select
                      className={SELECT}
                      value={editForm.company_id ?? ''}
                      onChange={e => setEdit('company_id', e.target.value ? Number(e.target.value) : null)}
                    >
                      <option value="">— Selecionar empresa —</option>
                      {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                )}

                <div className="border-t border-surface-600 pt-4">
                  <button
                    type="button"
                    onClick={() => { setShowPwSection(s => !s); setNewPw('') }}
                    className="text-xs text-violet-400 hover:text-violet-300 font-medium"
                  >
                    {showPwSection ? '— Cancelar redefinição de senha' : '+ Redefinir senha'}
                  </button>
                  {showPwSection && (
                    <div className="mt-3 relative">
                      <input
                        className={INPUT + ' pr-10'}
                        type={showPw ? 'text' : 'password'}
                        placeholder="Nova senha (mín. 6 caracteres)"
                        value={newPw}
                        onChange={e => setNewPw(e.target.value)}
                        minLength={6}
                      />
                      <button type="button" onClick={() => setShowPw(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                        {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs text-slate-500 pt-2">
                  <div className="bg-surface-700/50 rounded-xl p-3">
                    <p className="mb-0.5">Empresa</p>
                    <p className="text-slate-300 truncate">{detail.company_name ?? '—'}</p>
                  </div>
                  <div className="bg-surface-700/50 rounded-xl p-3">
                    <p className="mb-0.5">Criado em</p>
                    <p className="text-slate-300">{fmtDate(detail.created_at)}</p>
                  </div>
                </div>
              </div>
            ) : null}

            {detail && (
              <div className="shrink-0 border-t border-surface-600 p-4 space-y-2">
                <button
                  onClick={handleSaveEdit}
                  disabled={editSaving || !editDirty}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40"
                >
                  {editSaving && <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin" />}
                  {editSaving ? 'Salvando...' : 'Salvar alterações'}
                </button>
                <button
                  onClick={handleToggleActive}
                  disabled={actionLoading}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 ${
                    detail.is_active ? 'bg-surface-700 hover:bg-surface-600 text-slate-300' : 'bg-emerald-700 hover:bg-emerald-600 text-white'
                  }`}
                >
                  {actionLoading
                    ? <div className="w-4 h-4 border border-current border-t-transparent rounded-full animate-spin" />
                    : detail.is_active ? <ToggleLeft className="w-4 h-4" /> : <ToggleRight className="w-4 h-4" />
                  }
                  {detail.is_active ? 'Desativar usuário' : 'Ativar usuário'}
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {createOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-800 rounded-2xl border border-surface-600 w-full max-w-md shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-surface-600">
              <h2 className="text-white font-semibold">Novo Usuário</h2>
              <button onClick={() => setCreateOpen(false)} className="btn-ghost p-1.5 rounded-lg"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              {createError && (
                <div className="bg-red-500/15 border border-red-500/30 rounded-lg px-4 py-2.5 text-red-400 text-sm">{createError}</div>
              )}
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Nome completo *</label>
                <input required className={INPUT} value={createForm.name} onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))} placeholder="João Silva" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">E-mail *</label>
                <input required type="email" className={INPUT} value={createForm.email} onChange={e => setCreateForm(f => ({ ...f, email: e.target.value }))} placeholder="joao@empresa.com" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Senha * (mín. 6 caracteres)</label>
                <div className="relative">
                  <input
                    required type={showCreatePw ? 'text' : 'password'} minLength={6}
                    className={INPUT + ' pr-10'} value={createForm.password}
                    onChange={e => setCreateForm(f => ({ ...f, password: e.target.value }))}
                    placeholder="••••••••"
                  />
                  <button type="button" onClick={() => setShowCreatePw(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">
                    {showCreatePw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Papel *</label>
                <select
                  className={SELECT} value={createForm.role}
                  onChange={e => setCreateForm(f => ({ ...f, role: e.target.value, company_id: e.target.value === 'master_admin' ? null : f.company_id }))}
                >
                  {ALL_ROLES.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                </select>
              </div>
              {!isMasterRole(createForm.role) && (
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Empresa *</label>
                  <select
                    className={SELECT} value={createForm.company_id ?? ''}
                    onChange={e => setCreateForm(f => ({ ...f, company_id: e.target.value ? Number(e.target.value) : null }))}
                    required={!isMasterRole(createForm.role)}
                  >
                    <option value="">— Selecionar empresa —</option>
                    {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setCreateOpen(false)}
                  className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-400 hover:text-white bg-surface-700 hover:bg-surface-600 rounded-lg transition-colors">
                  Cancelar
                </button>
                <button type="submit" disabled={creating}
                  className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-violet-600 hover:bg-violet-500 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                  {creating && <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin" />}
                  {creating ? 'Criando...' : 'Criar Usuário'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
