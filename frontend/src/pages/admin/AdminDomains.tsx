import { useEffect, useState, useCallback } from 'react'
import {
  Globe, RefreshCw, Pencil, X, Save, ChevronRight,
  ToggleLeft, ToggleRight, CheckCircle2, AlertCircle, Code2,
} from 'lucide-react'
import {
  listDomains, getDomain, updateDomain, syncDomains,
  type DomainDefinitionListItem, type DomainDefinitionDetail, type UpdateDomainPayload,
} from '../../api/admin'

interface Toast { msg: string; type: 'success' | 'error' }

function ActivePill({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
      active ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-500/15 text-slate-400'
    }`}>
      {active ? <ToggleRight className="w-3 h-3" /> : <ToggleLeft className="w-3 h-3" />}
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function BuiltinBadge({ builtin }: { builtin: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
      builtin ? 'bg-violet-500/15 text-violet-400' : 'bg-amber-500/15 text-amber-400'
    }`}>
      {builtin ? 'Builtin' : 'Customizado'}
    </span>
  )
}

function JsonEditor({
  value,
  onChange,
}: {
  value: Record<string, unknown>
  onChange: (v: Record<string, unknown>) => void
}) {
  const [raw, setRaw] = useState(() => JSON.stringify(value, null, 2))
  const [error, setError] = useState('')

  useEffect(() => {
    setRaw(JSON.stringify(value, null, 2))
  }, [value])

  function handleChange(text: string) {
    setRaw(text)
    try {
      const parsed = JSON.parse(text)
      setError('')
      onChange(parsed)
    } catch {
      setError('JSON inválido')
    }
  }

  return (
    <div>
      <textarea
        value={raw}
        onChange={e => handleChange(e.target.value)}
        rows={18}
        spellCheck={false}
        className="w-full bg-surface-900 border border-surface-600 rounded-lg p-3 text-xs text-slate-300 font-mono resize-y focus:outline-none focus:border-violet-500"
      />
      {error && (
        <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" /> {error}
        </p>
      )}
    </div>
  )
}

export default function AdminDomains() {
  const [domains, setDomains] = useState<DomainDefinitionListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const [editKey, setEditKey] = useState<string | null>(null)
  const [detail, setDetail] = useState<DomainDefinitionDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [tab, setTab] = useState<'general' | 'config'>('general')

  const [form, setForm] = useState<UpdateDomainPayload>({})
  const [configDraft, setConfigDraft] = useState<Record<string, unknown>>({})
  const [saving, setSaving] = useState(false)

  const [toast, setToast] = useState<Toast | null>(null)

  function showToast(msg: string, type: 'success' | 'error') {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listDomains()
      setDomains(data)
    } catch {
      showToast('Erro ao carregar domínios', 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleSync() {
    setSyncing(true)
    try {
      const res = await syncDomains()
      showToast(`Sync concluído — ${res.created} criados, ${res.skipped} já existentes`, 'success')
      await load()
    } catch {
      showToast('Erro ao sincronizar domínios', 'error')
    } finally {
      setSyncing(false)
    }
  }

  async function openEdit(key: string) {
    setEditKey(key)
    setTab('general')
    setDetailLoading(true)
    try {
      const d = await getDomain(key)
      setDetail(d)
      setForm({ display_name: d.display_name, description: d.description ?? '', icon: d.icon ?? '', is_active: d.is_active })
      setConfigDraft(d.config_json)
    } catch {
      showToast('Erro ao carregar domínio', 'error')
      setEditKey(null)
    } finally {
      setDetailLoading(false)
    }
  }

  function closeEdit() {
    setEditKey(null)
    setDetail(null)
  }

  async function handleSave() {
    if (!detail) return
    setSaving(true)
    try {
      await updateDomain(detail.key, { ...form, config_json: configDraft })
      showToast('Domínio atualizado com sucesso', 'success')
      await load()
      closeEdit()
    } catch {
      showToast('Erro ao salvar domínio', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-medium ${
          toast.type === 'success' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/30'
        }`}>
          {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur border-b border-surface-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-violet-600/20 rounded-lg flex items-center justify-center">
            <Globe className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-base">Domínios de Serviço</h1>
            <p className="text-slate-500 text-xs">{domains.length} domínio{domains.length !== 1 ? 's' : ''} cadastrado{domains.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Sincronizando…' : 'Sincronizar'}
        </button>
      </div>

      {/* Table */}
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-500 text-sm">Carregando…</div>
        ) : domains.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-sm gap-3">
            <Globe className="w-8 h-8 opacity-30" />
            <p>Nenhum domínio cadastrado.</p>
            <button onClick={handleSync} disabled={syncing} className="btn-secondary text-sm">
              Sincronizar agora
            </button>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-600">
                  <th className="text-left text-slate-400 font-medium text-xs px-4 py-3">Domínio</th>
                  <th className="text-left text-slate-400 font-medium text-xs px-4 py-3 hidden md:table-cell">Tipo</th>
                  <th className="text-left text-slate-400 font-medium text-xs px-4 py-3">Status</th>
                  <th className="text-right text-slate-400 font-medium text-xs px-4 py-3">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-700">
                {domains.map(d => (
                  <tr key={d.key} className="hover:bg-surface-800/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <span className="text-xl leading-none">{d.icon ?? '🔧'}</span>
                        <div>
                          <p className="text-white font-medium">{d.display_name}</p>
                          <p className="text-slate-500 text-xs font-mono">{d.key}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <BuiltinBadge builtin={d.is_builtin} />
                    </td>
                    <td className="px-4 py-3">
                      <ActivePill active={d.is_active} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openEdit(d.key)}
                        className="inline-flex items-center gap-1.5 text-xs text-violet-400 hover:text-violet-300 transition-colors font-medium"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Drawer */}
      {editKey && (
        <div className="fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/50" onClick={closeEdit} />
          <div className="relative ml-auto w-full max-w-xl bg-surface-800 border-l border-surface-600 flex flex-col h-full shadow-2xl">
            {/* Drawer header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-600 shrink-0">
              <div className="flex items-center gap-3">
                <span className="text-2xl leading-none">{detail?.icon ?? '🔧'}</span>
                <div>
                  <h2 className="text-white font-semibold text-sm">{detail?.display_name ?? editKey}</h2>
                  <p className="text-slate-500 text-xs font-mono">{editKey}</p>
                </div>
              </div>
              <button onClick={closeEdit} className="text-slate-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-surface-600 shrink-0">
              {[
                { id: 'general', label: 'Geral' },
                { id: 'config', label: 'Configuração (JSON)' },
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id as typeof tab)}
                  className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                    tab === t.id
                      ? 'border-violet-500 text-violet-400'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  {t.id === 'config' && <Code2 className="inline w-3.5 h-3.5 mr-1.5 -mt-0.5" />}
                  {t.label}
                </button>
              ))}
            </div>

            {/* Drawer body */}
            <div className="flex-1 overflow-y-auto p-5">
              {detailLoading ? (
                <div className="flex items-center justify-center h-32 text-slate-500 text-sm">Carregando…</div>
              ) : (
                <>
                  {tab === 'general' && (
                    <div className="space-y-4">
                      <div>
                        <label className="label">Nome de exibição</label>
                        <input
                          type="text"
                          value={form.display_name ?? ''}
                          onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))}
                          className="input w-full"
                          placeholder="Ex: Redes de Proteção"
                        />
                      </div>
                      <div>
                        <label className="label">Ícone (emoji)</label>
                        <input
                          type="text"
                          value={form.icon ?? ''}
                          onChange={e => setForm(f => ({ ...f, icon: e.target.value }))}
                          className="input w-full"
                          placeholder="Ex: 🕸️"
                          maxLength={4}
                        />
                      </div>
                      <div>
                        <label className="label">Descrição</label>
                        <textarea
                          value={form.description ?? ''}
                          onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                          className="input w-full resize-none"
                          rows={3}
                          placeholder="Breve descrição do domínio de serviço"
                        />
                      </div>
                      <div>
                        <label className="label">Status</label>
                        <div className="flex gap-3">
                          {[true, false].map(v => (
                            <button
                              key={String(v)}
                              onClick={() => setForm(f => ({ ...f, is_active: v }))}
                              className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-all ${
                                form.is_active === v
                                  ? v ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400' : 'bg-red-500/20 border-red-500/50 text-red-400'
                                  : 'bg-transparent border-surface-600 text-slate-400 hover:border-surface-500'
                              }`}
                            >
                              {v ? 'Ativo' : 'Inativo'}
                            </button>
                          ))}
                        </div>
                      </div>
                      {detail && (
                        <div className="rounded-lg bg-surface-900 border border-surface-600 p-3 space-y-1 text-xs text-slate-500">
                          <div className="flex justify-between">
                            <span>Tipo</span>
                            <BuiltinBadge builtin={detail.is_builtin} />
                          </div>
                          <div className="flex justify-between">
                            <span>Key</span>
                            <span className="font-mono text-slate-400">{detail.key}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Criado em</span>
                            <span>{new Date(detail.created_at).toLocaleDateString('pt-BR')}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {tab === 'config' && (
                    <div className="space-y-3">
                      <p className="text-xs text-slate-500 leading-relaxed">
                        Este JSON contém configurações editáveis como mensagens do bot, serviços disponíveis,
                        valores padrão de onboarding e precificação. Alterações são salvas no banco e têm precedência
                        sobre os defaults do código.
                      </p>
                      <JsonEditor value={configDraft} onChange={setConfigDraft} />
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Drawer footer */}
            <div className="px-5 py-4 border-t border-surface-600 shrink-0 flex justify-end gap-3">
              <button onClick={closeEdit} className="btn-secondary text-sm">Cancelar</button>
              <button onClick={handleSave} disabled={saving || detailLoading} className="btn-primary flex items-center gap-2 text-sm">
                <Save className="w-4 h-4" />
                {saving ? 'Salvando…' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
