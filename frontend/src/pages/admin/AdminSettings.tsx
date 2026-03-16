import { useEffect, useState, useRef, useCallback } from 'react'
import {
  Globe, Mail, Phone, Building2, ToggleLeft, ToggleRight,
  Save, CheckCircle2, XCircle, Loader2, RefreshCw,
} from 'lucide-react'
import {
  getPlatformSettings, updatePlatformSettings,
  type PlatformSettings, type UpdatePlatformSettingsPayload,
} from '../../api/admin'

const DOMAIN_LABELS: Record<string, string> = {
  protection_network: 'Redes de Proteção',
  hvac: 'Climatização (HVAC)',
  electrician: 'Elétrica',
  plumbing: 'Hidráulica',
  cleaning: 'Limpeza',
}

interface Toast { msg: string; type: 'success' | 'error' }

function SectionCard({ icon: Icon, title, description, children }: {
  icon: React.ElementType; title: string; description: string; children: React.ReactNode
}) {
  return (
    <div className="card p-6">
      <div className="flex items-start gap-3 pb-4 border-b border-surface-600 mb-5">
        <div className="p-2 rounded-lg bg-violet-600/15 shrink-0">
          <Icon className="w-4 h-4 text-violet-400" />
        </div>
        <div>
          <h3 className="text-white font-semibold text-sm">{title}</h3>
          <p className="text-slate-500 text-xs mt-0.5">{description}</p>
        </div>
      </div>
      {children}
    </div>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-400 mb-1.5">{label}</label>
      {children}
      {hint && <p className="text-slate-600 text-xs mt-1">{hint}</p>}
    </div>
  )
}

const INPUT = "w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
const SELECT = "w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-violet-500"

export default function AdminSettings() {
  const [settings, setSettings] = useState<PlatformSettings | null>(null)
  const [form, setForm] = useState<UpdatePlatformSettingsPayload>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = useCallback((msg: string, type: Toast['type']) => {
    setToast({ msg, type })
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setToast(null), 3500)
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const s = await getPlatformSettings()
      setSettings(s)
      setForm({
        platform_name: s.platform_name,
        default_company_plan: s.default_company_plan ?? '',
        default_service_domain: s.default_service_domain,
        allow_self_signup: s.allow_self_signup,
        support_email: s.support_email ?? '',
        support_phone: s.support_phone ?? '',
        public_app_url: s.public_app_url ?? '',
        logo_url: s.logo_url ?? '',
      })
      setDirty(false)
    } catch {
      showToast('Erro ao carregar configurações.', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => { load() }, [load])

  function set<K extends keyof UpdatePlatformSettingsPayload>(key: K, value: UpdatePlatformSettingsPayload[K]) {
    setForm(f => ({ ...f, [key]: value }))
    setDirty(true)
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form }
      if (payload.support_email === '') delete payload.support_email
      if (payload.support_phone === '') delete payload.support_phone
      if (payload.public_app_url === '') delete payload.public_app_url
      if (payload.logo_url === '') delete payload.logo_url
      if (payload.default_company_plan === '') payload.default_company_plan = null
      const updated = await updatePlatformSettings(payload)
      setSettings(updated)
      setDirty(false)
      showToast('Configurações salvas com sucesso!', 'success')
    } catch {
      showToast('Erro ao salvar configurações.', 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 ${
          toast.type === 'error' ? 'bg-red-700 text-white' : 'bg-emerald-700 text-white'
        }`}>
          {toast.type === 'error' ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-white">Configurações SaaS</h1>
            <p className="text-slate-400 text-sm mt-0.5">Configurações globais da plataforma</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={load} className="btn-ghost p-2 rounded-lg" title="Recarregar">
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              form="settings-form"
              type="submit"
              disabled={saving || !dirty}
              className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {saving ? 'Salvando...' : dirty ? 'Salvar alterações' : 'Salvo'}
            </button>
          </div>
        </div>

        <form id="settings-form" onSubmit={handleSave} className="space-y-5">
          <SectionCard icon={Globe} title="Plataforma" description="Nome e URL pública da plataforma.">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Nome da plataforma">
                <input className={INPUT} value={form.platform_name ?? ''} onChange={e => set('platform_name', e.target.value)} placeholder="AlphaSync" />
              </Field>
              <Field label="URL pública" hint="Ex: https://app.alphasync.com.br">
                <input className={INPUT} value={form.public_app_url ?? ''} onChange={e => set('public_app_url', e.target.value)} placeholder="https://..." />
              </Field>
              <Field label="URL do logotipo" hint="Link público para o logo da plataforma.">
                <input className={INPUT} value={form.logo_url ?? ''} onChange={e => set('logo_url', e.target.value)} placeholder="https://cdn.../logo.png" />
              </Field>
            </div>
          </SectionCard>

          <SectionCard icon={Building2} title="Padrões de empresas" description="Valores padrão aplicados ao criar novas empresas.">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Plano padrão">
                <select className={SELECT} value={form.default_company_plan ?? ''} onChange={e => set('default_company_plan', e.target.value || null)}>
                  <option value="">— Sem plano padrão —</option>
                  {['starter', 'pro', 'enterprise'].map(p => (
                    <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                  ))}
                </select>
              </Field>
              <Field label="Domínio de serviço padrão">
                <select className={SELECT} value={form.default_service_domain ?? 'protection_network'} onChange={e => set('default_service_domain', e.target.value)}>
                  {Object.entries(DOMAIN_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </Field>
            </div>
            <div className="mt-4">
              <Field label="Auto-cadastro" hint="Permite que clientes criem empresas sem intervenção do master admin.">
                <button
                  type="button"
                  onClick={() => set('allow_self_signup', !form.allow_self_signup)}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border transition-colors ${
                    form.allow_self_signup
                      ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
                      : 'border-surface-500 bg-surface-700 text-slate-400 hover:text-slate-300'
                  }`}
                >
                  {form.allow_self_signup ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                  <span className="text-sm font-medium">
                    {form.allow_self_signup ? 'Auto-cadastro habilitado' : 'Auto-cadastro desabilitado'}
                  </span>
                </button>
              </Field>
            </div>
          </SectionCard>

          <SectionCard icon={Mail} title="Suporte & Contato" description="E-mail e telefone exibidos em notificações e para clientes.">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="E-mail de suporte">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input className={INPUT + ' pl-9'} type="email" value={form.support_email ?? ''} onChange={e => set('support_email', e.target.value)} placeholder="suporte@empresa.com" />
                </div>
              </Field>
              <Field label="Telefone de suporte">
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input className={INPUT + ' pl-9'} type="tel" value={form.support_phone ?? ''} onChange={e => set('support_phone', e.target.value)} placeholder="+55 11 99999-9999" />
                </div>
              </Field>
            </div>
          </SectionCard>

          {settings && (
            <div className="text-xs text-slate-600 px-1 flex gap-4">
              <span>Criado: {new Date(settings.created_at).toLocaleString('pt-BR')}</span>
              <span>Atualizado: {new Date(settings.updated_at).toLocaleString('pt-BR')}</span>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
