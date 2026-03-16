import { useEffect, useState, useRef, useCallback } from 'react'
import {
  Globe, Mail, Phone, Building2, Save, CheckCircle2, XCircle,
  Loader2, RefreshCw, Link, AlertCircle,
} from 'lucide-react'
import {
  getPlatformSettings, updatePlatformSettings,
  type PlatformSettings, type UpdatePlatformSettingsPayload,
} from '../../api/admin'

const ALL_DOMAINS: Record<string, string> = {
  protection_network: 'Redes de Proteção',
  hvac: 'Climatização (HVAC)',
  electrician: 'Elétrica',
  plumbing: 'Hidráulica',
  cleaning: 'Limpeza',
  glass_installation: 'Vidraçaria',
  pest_control: 'Dedetização',
  security_cameras: 'Câmeras de Segurança',
}

interface Toast { msg: string; type: 'success' | 'error' }

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex w-11 h-6 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-surface-800 ${
        checked ? 'bg-emerald-500' : 'bg-surface-600'
      }`}
    >
      <span className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${
        checked ? 'translate-x-5' : 'translate-x-0'
      }`} />
    </button>
  )
}

function SectionCard({ icon: Icon, title, description, children }: {
  icon: React.ElementType; title: string; description: string; children: React.ReactNode
}) {
  return (
    <div className="card p-6">
      <div className="flex items-start gap-4 pb-5 border-b border-surface-600 mb-5">
        <div className="w-9 h-9 bg-violet-600/15 border border-violet-500/25 rounded-xl flex items-center justify-center shrink-0">
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
      <label className="label">{label}</label>
      {children}
      {hint && <p className="text-slate-600 text-xs mt-1">{hint}</p>}
    </div>
  )
}

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
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl text-sm font-medium backdrop-blur border ${
          toast.type === 'error' ? 'bg-red-500/20 text-red-300 border-red-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
        }`}>
          {toast.type === 'error' ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      {/* Sticky header */}
      <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur border-b border-surface-700 px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-violet-600/20 rounded-lg flex items-center justify-center">
            <Globe className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-base">Configurações SaaS</h1>
            <p className="text-slate-500 text-xs">Configurações globais da plataforma AlphaSync</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {dirty && (
            <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/25 px-2.5 py-1 rounded-full font-medium flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> Alterações pendentes
            </span>
          )}
          <button onClick={load} className="btn-secondary px-3 py-2 text-sm" title="Recarregar">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            form="settings-form"
            type="submit"
            disabled={saving || !dirty}
            className={`flex items-center gap-2 text-sm px-4 py-2 rounded-lg font-medium transition-all ${
              dirty ? 'btn-primary' : 'bg-surface-700 text-slate-500 cursor-not-allowed'
            }`}
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? 'Salvando…' : dirty ? 'Salvar alterações' : 'Salvo'}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto">
          <form id="settings-form" onSubmit={handleSave} className="space-y-5">

            {/* Platform */}
            <SectionCard icon={Globe} title="Plataforma" description="Nome, URL pública e logo da plataforma.">
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="Nome da plataforma">
                    <input className="input" value={form.platform_name ?? ''} onChange={e => set('platform_name', e.target.value)} placeholder="AlphaSync" />
                  </Field>
                  <Field label="URL pública" hint="Ex: https://app.alphasync.com.br">
                    <div className="relative">
                      <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                      <input className="input pl-9" value={form.public_app_url ?? ''} onChange={e => set('public_app_url', e.target.value)} placeholder="https://..." />
                    </div>
                  </Field>
                </div>
                <Field label="URL do logotipo" hint="Link público para o logo da plataforma (PNG ou SVG recomendado).">
                  <input className="input" value={form.logo_url ?? ''} onChange={e => set('logo_url', e.target.value)} placeholder="https://cdn.../logo.png" />
                </Field>
              </div>
            </SectionCard>

            {/* Company defaults */}
            <SectionCard icon={Building2} title="Padrões de empresas" description="Valores padrão aplicados ao criar novas empresas.">
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="Plano padrão">
                    <select className="input" value={form.default_company_plan ?? ''} onChange={e => set('default_company_plan', e.target.value || null)}>
                      <option value="">— Sem plano padrão —</option>
                      {['starter', 'pro', 'enterprise'].map(p => (
                        <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Domínio de serviço padrão">
                    <select className="input" value={form.default_service_domain ?? 'protection_network'} onChange={e => set('default_service_domain', e.target.value)}>
                      {Object.entries(ALL_DOMAINS).map(([v, l]) => (
                        <option key={v} value={v}>{l}</option>
                      ))}
                    </select>
                  </Field>
                </div>
                <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-surface-900 border border-surface-600">
                  <div>
                    <p className="text-white text-sm font-medium">Auto-cadastro de empresas</p>
                    <p className="text-slate-500 text-xs mt-0.5">Permite que clientes criem empresas sem intervenção do master admin</p>
                  </div>
                  <Toggle checked={!!form.allow_self_signup} onChange={v => set('allow_self_signup', v)} />
                </div>
              </div>
            </SectionCard>

            {/* Support */}
            <SectionCard icon={Mail} title="Suporte & Contato" description="E-mail e telefone exibidos em notificações e para clientes.">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="E-mail de suporte">
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input className="input pl-9" type="email" value={form.support_email ?? ''} onChange={e => set('support_email', e.target.value)} placeholder="suporte@empresa.com" />
                  </div>
                </Field>
                <Field label="Telefone de suporte">
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input className="input pl-9" type="tel" value={form.support_phone ?? ''} onChange={e => set('support_phone', e.target.value)} placeholder="+55 11 99999-9999" />
                  </div>
                </Field>
              </div>
            </SectionCard>

            {/* Timestamps */}
            {settings && (
              <div className="card divide-y divide-surface-600">
                <div className="flex justify-between items-center px-5 py-3 text-xs">
                  <span className="text-slate-500">Criado em</span>
                  <span className="text-slate-400">{new Date(settings.created_at).toLocaleString('pt-BR')}</span>
                </div>
                <div className="flex justify-between items-center px-5 py-3 text-xs">
                  <span className="text-slate-500">Última atualização</span>
                  <span className="text-slate-400">{new Date(settings.updated_at).toLocaleString('pt-BR')}</span>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}
