import { useEffect, useState } from 'react'
import {
  Settings as SettingsIcon, Save, Bot, Palette, Globe,
  AlertCircle, CheckCircle, Shield, Eye, EyeOff, Plus, X,
  CalendarDays, UserCheck, ChevronDown, ChevronUp, RotateCcw, ShieldCheck,
} from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { PageSpinner } from '../components/ui/Spinner'
import { getCompanySettings, updateCompanySettings } from '../api/company'
import { getPNSettings, updatePNSettings } from '../api/measures'
import {
  listInstallers, updateInstallerSchedule,
  getScheduleConfig, updateScheduleConfig,
  getFlowConfig, updateFlowConfig,
} from '../api/company'
import type {
  InstallerWithSchedule, InstallerScheduleConfig,
  ScheduleConfig, DomainFlowConfig, DomainBotMessages,
} from '../api/company'
import type { CompanySettings, PNSettings } from '../types'

const TIMEZONES = ['America/Sao_Paulo', 'America/Manaus', 'America/Belem', 'America/Fortaleza', 'America/Recife']
const CURRENCIES = ['BRL', 'USD', 'EUR']
const SLOT_OPTIONS = [
  { value: 60, label: '1 hora' },
  { value: 90, label: '1h 30min' },
  { value: 120, label: '2 horas' },
  { value: 180, label: '3 horas' },
  { value: 240, label: '4 horas' },
]
const WEEKDAY_LABELS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
const TONE_OPTIONS = ['amigável', 'profissional', 'objetivo', 'técnico', 'descontraído']

type Tab = 'empresa' | 'protection_network' | 'agendamento' | 'fluxo_bot' | 'garantia'

interface MeshEntry {
  id: string
  label: string
  active: boolean
  colors: string[]
  price_per_m2: number | null
}

interface SectionProps { title: string; icon: React.ReactNode; children: React.ReactNode }
function Section({ title, icon, children }: SectionProps) {
  return (
    <div className="card p-6">
      <div className="flex items-center gap-2.5 mb-5 pb-4 border-b border-surface-600">
        <div className="w-7 h-7 bg-brand-500/15 rounded-lg flex items-center justify-center text-brand-400">
          {icon}
        </div>
        <h3 className="text-white font-semibold text-sm">{title}</h3>
      </div>
      {children}
    </div>
  )
}

interface FieldProps { label: string; hint?: string; children: React.ReactNode }
function Field({ label, hint, children }: FieldProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-start py-3 border-b border-surface-700 last:border-0">
      <div className="pt-1.5">
        <label className="text-slate-400 text-sm font-medium block">{label}</label>
        {hint && <p className="text-slate-600 text-xs mt-0.5">{hint}</p>}
      </div>
      <div className="sm:col-span-2">{children}</div>
    </div>
  )
}

function TagInput({ values, onChange, placeholder }: {
  values: string[]
  onChange: (v: string[]) => void
  placeholder?: string
}) {
  const [input, setInput] = useState('')
  function add() {
    const val = input.trim().toLowerCase()
    if (val && !values.includes(val)) onChange([...values, val])
    setInput('')
  }
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {values.map((v) => (
          <span key={v} className="flex items-center gap-1 bg-brand-500/15 text-brand-300 text-xs px-2 py-1 rounded-full">
            {v}
            <button onClick={() => onChange(values.filter((x) => x !== v))} className="text-brand-500 hover:text-brand-300">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="input flex-1 text-sm"
          placeholder={placeholder || 'Adicionar...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add() } }}
        />
        <button onClick={add} className="btn-secondary px-3">
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

function parseOptionalNumber(value: string): number | null {
  const normalized = value.trim().replace(',', '.')
  if (!normalized) return null
  const parsed = parseFloat(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

export default function Settings() {
  const [tab, setTab] = useState<Tab>('empresa')
  const [settings, setSettings] = useState<CompanySettings | null>(null)
  const [pnSettings, setPnSettings] = useState<PNSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [form, setForm] = useState<Partial<CompanySettings>>({})
  const [pnForm, setPnForm] = useState<Partial<PNSettings>>({})

  const [installers, setInstallers] = useState<InstallerWithSchedule[]>([])
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    slot_minutes: 120, workday_start: '08:00', workday_end: '18:00', allowed_weekdays: [0, 1, 2, 3, 4],
  })
  const [installerSchedules, setInstallerSchedules] = useState<Record<number, InstallerScheduleConfig>>({})
  const [savingInstaller, setSavingInstaller] = useState<number | null>(null)

  const [flowConfigs, setFlowConfigs] = useState<DomainFlowConfig[]>([])
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null)
  const [flowForms, setFlowForms] = useState<Record<string, DomainBotMessages>>({})
  const [savingDomain, setSavingDomain] = useState<string | null>(null)

  const [warrantyForm, setWarrantyForm] = useState({
    service_description: '',
    warranty_period: '12 meses',
    warranty_covers: '',
    additional_notes: '',
    signature: '',
  })
  const [savingWarranty, setSavingWarranty] = useState(false)
  const [meshCatalog, setMeshCatalog] = useState<MeshEntry[]>([])
  const [savingMesh, setSavingMesh] = useState(false)
  const [newMeshId, setNewMeshId] = useState('')
  const [newMeshLabel, setNewMeshLabel] = useState('')

  useEffect(() => {
    Promise.all([getCompanySettings(), getPNSettings()])
      .then(([s, pn]) => {
        setSettings(s)
        setPnSettings(pn)
        setForm({
          brand_name: s.brand_name ?? '',
          bot_name: s.bot_name ?? '',
          quote_prefix: s.quote_prefix ?? '',
          primary_color: s.primary_color ?? '',
          currency: s.currency,
          timezone: s.timezone,
          logo_url: s.logo_url ?? '',
          whatsapp_verify_token: s.whatsapp_verify_token ?? '',
          whatsapp_access_token: s.whatsapp_access_token ?? '',
          whatsapp_phone_number_id: s.whatsapp_phone_number_id ?? '',
        })
        setPnForm({ ...pn })
        const catalog = (s.extra_settings as { mesh_catalog?: MeshEntry[] } | undefined)?.mesh_catalog
        if (catalog && Array.isArray(catalog) && catalog.length > 0) {
          setMeshCatalog(
            catalog.map((mesh) => ({
              id: mesh.id,
              label: mesh.label,
              active: mesh.active,
              colors: Array.isArray(mesh.colors) ? mesh.colors : [],
              price_per_m2: mesh.price_per_m2 ?? null,
            }))
          )
        } else {
          const meshTypes: string[] = Array.isArray(pn.available_mesh_types) ? pn.available_mesh_types : []
          setMeshCatalog(
            meshTypes.map((id) => ({
              id,
              label: id,
              active: true,
              colors: [],
              price_per_m2: null,
            }))
          )
        }
      })
      .catch(() => setToast({ type: 'error', msg: 'Erro ao carregar configurações.' }))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (tab === 'agendamento') {
      Promise.all([listInstallers(), getScheduleConfig()])
        .then(([inst, cfg]) => {
          setInstallers(inst)
          setScheduleConfig(cfg)
          const schedules: Record<number, InstallerScheduleConfig> = {}
          inst.forEach(i => { schedules[i.id] = { ...i.schedule } })
          setInstallerSchedules(schedules)
        })
        .catch(() => showToast('error', 'Erro ao carregar configurações de agendamento.'))
    } else if (tab === 'fluxo_bot') {
      getFlowConfig()
        .then(configs => {
          setFlowConfigs(configs)
          const forms: Record<string, DomainBotMessages> = {}
          configs.forEach(c => { forms[c.key] = { ...c.messages } })
          setFlowForms(forms)
        })
        .catch(() => showToast('error', 'Erro ao carregar configurações do fluxo.'))
    } else if (tab === 'garantia') {
      getCompanySettings()
        .then(s => {
          const wCfg = (s as any).extra_settings?.warranty ?? {}
          setWarrantyForm({
            service_description: wCfg.service_description ?? '',
            warranty_period: wCfg.warranty_period ?? '12 meses',
            warranty_covers: wCfg.warranty_covers ?? '',
            additional_notes: wCfg.additional_notes ?? '',
            signature: wCfg.signature ?? '',
          })
        })
        .catch(() => showToast('error', 'Erro ao carregar configurações de garantia.'))
    }
  }, [tab])

  function showToast(type: 'success' | 'error', msg: string) {
    setToast({ type, msg })
    setTimeout(() => setToast(null), 4000)
  }

  async function handleSave() {
    setSaving(true)
    setToast(null)
    try {
      const updated = await updateCompanySettings({
        brand_name: form.brand_name || null,
        bot_name: form.bot_name || null,
        quote_prefix: form.quote_prefix || null,
        primary_color: form.primary_color || null,
        currency: form.currency,
        timezone: form.timezone,
        logo_url: form.logo_url || null,
        whatsapp_verify_token: form.whatsapp_verify_token || null,
        whatsapp_access_token: form.whatsapp_access_token || null,
        whatsapp_phone_number_id: form.whatsapp_phone_number_id || null,
      })
      setSettings(updated)
      showToast('success', 'Configurações salvas com sucesso!')
    } catch {
      showToast('error', 'Erro ao salvar. Tente novamente.')
    } finally {
      setSaving(false)
    }
  }

  async function handleSavePN() {
    setSaving(true)
    setToast(null)
    try {
      const updated = await updatePNSettings(pnForm)
      setPnSettings(updated)
      setPnForm({ ...updated })
      showToast('success', 'Configurações Protection Network salvas!')
    } catch {
      showToast('error', 'Erro ao salvar configurações PN.')
    } finally {
      setSaving(false)
    }
  }

  async function handleSaveScheduleConfig() {
    setSaving(true)
    try {
      const updated = await updateScheduleConfig(scheduleConfig)
      setScheduleConfig(updated)
      showToast('success', 'Configuração de horários salva!')
    } catch {
      showToast('error', 'Erro ao salvar configuração de horários.')
    } finally {
      setSaving(false)
    }
  }

  async function handleSaveInstallerSchedule(userId: number) {
    const cfg = installerSchedules[userId]
    if (!cfg) return
    setSavingInstaller(userId)
    try {
      const updated = await updateInstallerSchedule(userId, cfg)
      setInstallers(prev => prev.map(i => i.id === userId ? { ...i, schedule: updated.schedule } : i))
      showToast('success', 'Disponibilidade do instalador salva!')
    } catch {
      showToast('error', 'Erro ao salvar disponibilidade.')
    } finally {
      setSavingInstaller(null)
    }
  }

  async function handleSaveDomainFlow(key: string) {
    const msgs = flowForms[key]
    if (!msgs) return
    setSavingDomain(key)
    try {
      const updated = await updateFlowConfig(key, msgs)
      setFlowConfigs(prev => prev.map(c => c.key === key ? updated : c))
      showToast('success', 'Mensagens do fluxo salvas!')
    } catch {
      showToast('error', 'Erro ao salvar mensagens.')
    } finally {
      setSavingDomain(null)
    }
  }

  async function handleSaveWarranty() {
    setSavingWarranty(true)
    try {
      await updateCompanySettings({ extra_settings: { warranty: warrantyForm } } as any)
      showToast('success', 'Configurações de garantia salvas!')
    } catch {
      showToast('error', 'Erro ao salvar configurações de garantia.')
    } finally {
      setSavingWarranty(false)
    }
  }

  async function handleSaveMeshCatalog() {
    setSavingMesh(true)
    try {
      await updateCompanySettings({ extra_settings: { mesh_catalog: meshCatalog } } as any)
      showToast('success', 'Catálogo de malhas salvo!')
    } catch {
      showToast('error', 'Erro ao salvar catálogo de malhas.')
    } finally {
      setSavingMesh(false)
    }
  }

  function addMeshEntry() {
    const id = newMeshId.trim().toLowerCase().replace(/\s+/g, '')
    const label = newMeshLabel.trim() || id
    if (!id || meshCatalog.some(m => m.id === id)) return
    setMeshCatalog(prev => [...prev, { id, label, active: true, colors: [], price_per_m2: null }])
    setNewMeshId('')
    setNewMeshLabel('')
  }

  function field(key: keyof CompanySettings) {
    return {
      value: (form[key] as string) ?? '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
        setForm((prev) => ({ ...prev, [key]: e.target.value })),
    }
  }

  function toggleWeekday(day: number, target: 'schedule' | number) {
    if (target === 'schedule') {
      const current = scheduleConfig.allowed_weekdays
      const updated = current.includes(day) ? current.filter(d => d !== day) : [...current, day].sort()
      setScheduleConfig(prev => ({ ...prev, allowed_weekdays: updated }))
    } else {
      const userId = target as number
      const current = installerSchedules[userId]?.allowed_weekdays ?? [0, 1, 2, 3, 4]
      const updated = current.includes(day) ? current.filter(d => d !== day) : [...current, day].sort()
      setInstallerSchedules(prev => ({
        ...prev,
        [userId]: { ...prev[userId], allowed_weekdays: updated },
      }))
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar title="Configurações" />
        <div className="flex-1 flex items-center justify-center"><PageSpinner /></div>
      </div>
    )
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: 'empresa', label: 'Empresa' },
    { key: 'protection_network', label: 'Protection Network' },
    { key: 'agendamento', label: 'Agendamento' },
    { key: 'fluxo_bot', label: 'Fluxo do Bot' },
    { key: 'garantia', label: 'Garantia' },
  ]

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title="Configurações" subtitle="Configurações da empresa" />
      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl space-y-5">
          {toast && (
            <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm ${
              toast.type === 'success'
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/10 border border-red-500/20 text-red-400'
            }`}>
              {toast.type === 'success'
                ? <CheckCircle className="w-4 h-4 shrink-0" />
                : <AlertCircle className="w-4 h-4 shrink-0" />}
              {toast.msg}
            </div>
          )}

          <div className="flex gap-1 p-1 bg-surface-800 border border-surface-600 rounded-xl w-fit flex-wrap">
            {TABS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  tab === key
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {tab === 'empresa' && (
            <>
              <Section title="Identidade da empresa" icon={<SettingsIcon className="w-4 h-4" />}>
                <Field label="Nome da marca">
                  <input className="input" placeholder="AlphaSync" {...field('brand_name')} />
                </Field>
                <Field label="Logo URL">
                  <input className="input" placeholder="https://..." {...field('logo_url')} />
                </Field>
                <Field label="Cor primária">
                  <div className="flex gap-2">
                    <input type="color" className="w-9 h-9 rounded bg-surface-700 border border-surface-500 cursor-pointer" {...field('primary_color')} />
                    <input className="input" placeholder="#6366f1" {...field('primary_color')} />
                  </div>
                </Field>
                <Field label="Prefixo de orçamento">
                  <input className="input" placeholder="ORC-" {...field('quote_prefix')} />
                </Field>
              </Section>

              <Section title="Chatbot" icon={<Bot className="w-4 h-4" />}>
                <Field label="Nome do bot">
                  <input className="input" placeholder="AlphaBot" {...field('bot_name')} />
                </Field>
                <Field label="ID do número WhatsApp" hint="Phone Number ID da Meta (para envio de mensagens)">
                  <input className="input" placeholder="123456789012345" {...field('whatsapp_phone_number_id')} />
                </Field>
                <Field label="Token de acesso WhatsApp" hint="Access Token da API do WhatsApp Business">
                  <input className="input" type="password" placeholder="••••••••" {...field('whatsapp_access_token')} />
                </Field>
                <Field label="Token de verificação WhatsApp" hint="Usado para validar o webhook">
                  <input className="input" type="password" placeholder="••••••••" {...field('whatsapp_verify_token')} />
                </Field>
                {!!(settings?.extra_settings?.bot) && (
                  <div className="mt-4 bg-surface-700/50 rounded-lg p-4">
                    <p className="text-slate-400 text-xs font-semibold uppercase tracking-wide mb-3">Módulos habilitados</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(settings.extra_settings.bot as Record<string, boolean>)
                        .filter(([k]) => k !== 'enabled')
                        .map(([key, val]) => (
                          <div key={key} className="flex items-center gap-2">
                            <div className={`w-1.5 h-1.5 rounded-full ${val ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                            <span className="text-slate-400 text-xs capitalize">{key.replace(/_/g, ' ')}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </Section>

              <Section title="Regional" icon={<Globe className="w-4 h-4" />}>
                <Field label="Fuso horário">
                  <select className="input" {...field('timezone')}>
                    {TIMEZONES.map((tz) => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Moeda">
                  <select className="input" {...field('currency')}>
                    {CURRENCIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </Field>
              </Section>

              {settings?.extra_settings?.pricing_rules && (
                <Section title="Regras de precificação" icon={<Palette className="w-4 h-4" />}>
                  <div className="space-y-2">
                    {Object.entries(settings.extra_settings.pricing_rules as Record<string, unknown>).map(([key, val]) => (
                      <div key={key} className="flex justify-between items-center py-2 border-b border-surface-700 last:border-0">
                        <span className="text-slate-400 text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="text-white text-sm font-medium font-mono">
                          {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-slate-600 text-xs mt-3">
                    Edição avançada disponível na aba Protection Network.
                  </p>
                </Section>
              )}

              <div className="flex justify-end pt-2">
                <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2 px-6">
                  {saving ? (
                    <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Salvando...</>
                  ) : (
                    <><Save className="w-4 h-4" />Salvar configurações</>
                  )}
                </button>
              </div>
            </>
          )}

          {tab === 'protection_network' && pnForm && (
            <>
              <Section title="Protection Network" icon={<Shield className="w-4 h-4" />}>
                <div className={`mb-5 flex items-start gap-3 p-4 rounded-xl border ${
                  pnForm.show_measures_to_customer
                    ? 'bg-emerald-500/10 border-emerald-500/20'
                    : 'bg-yellow-500/10 border-yellow-500/20'
                }`}>
                  <div className={`mt-0.5 ${pnForm.show_measures_to_customer ? 'text-emerald-400' : 'text-yellow-400'}`}>
                    {pnForm.show_measures_to_customer ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                  </div>
                  <div className="flex-1">
                    <p className={`font-semibold text-sm ${pnForm.show_measures_to_customer ? 'text-emerald-400' : 'text-yellow-400'}`}>
                      {pnForm.show_measures_to_customer
                        ? 'Medidas visíveis para o cliente'
                        : '⚠️ Medidas ocultadas do cliente — usadas apenas para cálculo interno.'}
                    </p>
                    <p className="text-slate-400 text-xs mt-0.5">
                      {pnForm.show_measures_to_customer
                        ? 'O bot pode exibir e listar medidas cadastradas durante o atendimento.'
                        : 'O bot não exibirá listas, nomes de áreas, quantidades ou títulos de itens ao cliente.'}
                    </p>
                  </div>
                  <button
                    onClick={() => setPnForm((f) => ({ ...f, show_measures_to_customer: !f.show_measures_to_customer }))}
                    className={`w-12 h-6 rounded-full transition-colors flex items-center shrink-0 ${
                      pnForm.show_measures_to_customer ? 'bg-emerald-500 justify-end' : 'bg-slate-600 justify-start'
                    }`}
                  >
                    <span className="w-5 h-5 bg-white rounded-full mx-0.5 shadow" />
                  </button>
                </div>

                <Field label="Preço padrão por m²">
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">R$</span>
                    <input
                      type="number" min="0" step="0.01"
                      className="input pl-9"
                      value={pnForm.default_price_per_m2 ?? ''}
                      onChange={(e) => setPnForm((f) => ({ ...f, default_price_per_m2: parseFloat(e.target.value) }))}
                    />
                  </div>
                </Field>
                <Field label="Valor mínimo do pedido">
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">R$</span>
                    <input
                      type="number" min="0" step="0.01"
                      className="input pl-9"
                      value={pnForm.minimum_order_value ?? ''}
                      onChange={(e) => setPnForm((f) => ({ ...f, minimum_order_value: parseFloat(e.target.value) }))}
                    />
                  </div>
                </Field>
                <Field label="Taxa de visita">
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">R$</span>
                    <input
                      type="number" min="0" step="0.01"
                      className="input pl-9"
                      value={pnForm.visit_fee ?? ''}
                      onChange={(e) => setPnForm((f) => ({ ...f, visit_fee: parseFloat(e.target.value) }))}
                    />
                  </div>
                </Field>
                <Field label="Cores disponíveis">
                  <TagInput
                    values={pnForm.available_colors ?? []}
                    onChange={(v) => setPnForm((f) => ({ ...f, available_colors: v }))}
                    placeholder="Ex: branca, preta..."
                  />
                </Field>
                <Field label="Malhas disponíveis">
                  <TagInput
                    values={pnForm.available_mesh_types ?? []}
                    onChange={(v) => setPnForm((f) => ({ ...f, available_mesh_types: v }))}
                    placeholder="Ex: 3x3, 5x5..."
                  />
                </Field>
              </Section>

              <div className="flex justify-end pt-2">
                <button onClick={handleSavePN} disabled={saving} className="btn-primary flex items-center gap-2 px-6">
                  {saving ? (
                    <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Salvando...</>
                  ) : (
                    <><Save className="w-4 h-4" />Salvar Protection Network</>
                  )}
                </button>
              </div>

              <Section title="Catálogo de Malhas" icon={<Shield className="w-4 h-4" />}>
                <p className="text-slate-500 text-xs mb-4">Defina as malhas disponíveis com rótulos amigáveis, cores específicas e preço por m² por malha. Usado no bot para exibir opções ao cliente.</p>
                <div className="space-y-3">
                  {meshCatalog.map((mesh, idx) => (
                    <div key={mesh.id} className={`rounded-xl border p-4 space-y-3 ${mesh.active ? 'border-surface-600 bg-surface-800' : 'border-surface-700 opacity-60'}`}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2 min-w-0">
                          <button
                            onClick={() => setMeshCatalog(prev => prev.map((m, i) => i === idx ? { ...m, active: !m.active } : m))}
                            className={`w-9 h-5 rounded-full transition-colors flex items-center shrink-0 ${mesh.active ? 'bg-emerald-500 justify-end' : 'bg-slate-600 justify-start'}`}
                          >
                            <span className="w-4 h-4 bg-white rounded-full mx-0.5 shadow" />
                          </button>
                          <span className="text-slate-400 text-xs font-mono bg-surface-700 px-2 py-0.5 rounded">{mesh.id}</span>
                        </div>
                        <button
                          onClick={() => setMeshCatalog(prev => prev.filter((_, i) => i !== idx))}
                          className="text-slate-600 hover:text-red-400 transition-colors p-1"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                      <div>
                        <label className="text-slate-500 text-xs mb-1 block">Rótulo exibido ao cliente</label>
                        <input
                          className="input text-sm"
                          placeholder={`Ex: ${mesh.id} — Descrição amigável`}
                          value={mesh.label}
                          onChange={e => setMeshCatalog(prev => prev.map((m, i) => i === idx ? { ...m, label: e.target.value } : m))}
                        />
                      </div>
                      <div>
                        <label className="text-slate-500 text-xs mb-1 block">Preço por m² desta malha (opcional)</label>
                        <div className="relative">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">R$</span>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            className="input pl-9 text-sm"
                            placeholder="Ex: 45,00"
                            value={mesh.price_per_m2 ?? ''}
                            onChange={e =>
                              setMeshCatalog(prev =>
                                prev.map((m, i) =>
                                  i === idx ? { ...m, price_per_m2: parseOptionalNumber(e.target.value) } : m
                                )
                              )
                            }
                          />
                        </div>
                        <p className="text-slate-600 text-[11px] mt-1">
                          Deixe vazio para usar o preço padrão por m².
                        </p>
                      </div>
                      <div>
                        <label className="text-slate-500 text-xs mb-1 block">Cores específicas desta malha (deixe vazio para usar todas)</label>
                        <TagInput
                          values={mesh.colors}
                          onChange={colors => setMeshCatalog(prev => prev.map((m, i) => i === idx ? { ...m, colors } : m))}
                          placeholder="Ex: branca, preta..."
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-4 pt-4 border-t border-surface-700">
                  <p className="text-slate-500 text-xs mb-3 font-medium">Adicionar nova malha</p>
                  <div className="flex gap-2 flex-wrap">
                    <input
                      className="input text-sm w-28"
                      placeholder="ID (ex: 3x3)"
                      value={newMeshId}
                      onChange={e => setNewMeshId(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addMeshEntry() } }}
                    />
                    <input
                      className="input text-sm flex-1 min-w-[160px]"
                      placeholder="Rótulo (ex: 3x3 — Gatos e pássaros)"
                      value={newMeshLabel}
                      onChange={e => setNewMeshLabel(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addMeshEntry() } }}
                    />
                    <button onClick={addMeshEntry} disabled={!newMeshId.trim()} className="btn-secondary px-4 flex items-center gap-1.5 text-sm">
                      <Plus className="w-4 h-4" />
                      Adicionar
                    </button>
                  </div>
                </div>

                <div className="flex justify-end mt-4">
                  <button onClick={handleSaveMeshCatalog} disabled={savingMesh} className="btn-primary flex items-center gap-2 px-5">
                    {savingMesh ? (
                      <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Salvando...</>
                    ) : (
                      <><Save className="w-4 h-4" />Salvar catálogo</>
                    )}
                  </button>
                </div>
              </Section>
            </>
          )}

          {tab === 'agendamento' && (
            <>
              <Section title="Horários de funcionamento" icon={<CalendarDays className="w-4 h-4" />}>
                <Field label="Duração do bloco" hint="Tempo padrão de cada agendamento">
                  <select
                    className="input"
                    value={scheduleConfig.slot_minutes}
                    onChange={(e) => setScheduleConfig(prev => ({ ...prev, slot_minutes: Number(e.target.value) }))}
                  >
                    {SLOT_OPTIONS.map(o => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Início do expediente">
                  <input
                    type="time"
                    className="input"
                    value={scheduleConfig.workday_start}
                    onChange={(e) => setScheduleConfig(prev => ({ ...prev, workday_start: e.target.value }))}
                  />
                </Field>
                <Field label="Fim do expediente">
                  <input
                    type="time"
                    className="input"
                    value={scheduleConfig.workday_end}
                    onChange={(e) => setScheduleConfig(prev => ({ ...prev, workday_end: e.target.value }))}
                  />
                </Field>
                <Field label="Dias de trabalho">
                  <div className="flex gap-2 flex-wrap">
                    {WEEKDAY_LABELS.map((label, idx) => (
                      <button
                        key={idx}
                        onClick={() => toggleWeekday(idx, 'schedule')}
                        className={`w-10 h-10 rounded-xl text-xs font-semibold border transition-all ${
                          scheduleConfig.allowed_weekdays.includes(idx)
                            ? 'bg-brand-600 text-white border-brand-500'
                            : 'bg-surface-700 text-slate-500 border-surface-600 hover:border-surface-500'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </Field>
                <div className="pt-3 flex justify-end">
                  <button onClick={handleSaveScheduleConfig} disabled={saving} className="btn-primary flex items-center gap-2">
                    {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save className="w-4 h-4" />}
                    {saving ? 'Salvando...' : 'Salvar horários'}
                  </button>
                </div>
              </Section>

              <Section title="Disponibilidade por instalador" icon={<UserCheck className="w-4 h-4" />}>
                {installers.length === 0 ? (
                  <div className="text-center py-8">
                    <UserCheck className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-500 text-sm">Nenhum instalador cadastrado.</p>
                    <p className="text-slate-600 text-xs mt-1">Cadastre instaladores em Usuários para configurar disponibilidade.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {installers.map(installer => {
                      const cfg = installerSchedules[installer.id] ?? installer.schedule
                      return (
                        <div key={installer.id} className="bg-surface-700/50 rounded-xl p-4 border border-surface-600">
                          <div className="flex items-center gap-3 mb-4">
                            <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 font-semibold text-sm shrink-0">
                              {installer.name.charAt(0).toUpperCase()}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-white text-sm font-medium">{installer.name}</p>
                              <p className="text-slate-500 text-xs">{installer.email}</p>
                            </div>
                            {!installer.is_active && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">Inativo</span>
                            )}
                          </div>
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <label className="text-slate-500 text-xs mb-1 block">Início</label>
                                <input
                                  type="time"
                                  className="input text-sm"
                                  value={cfg.work_start}
                                  onChange={(e) => setInstallerSchedules(prev => ({
                                    ...prev,
                                    [installer.id]: { ...prev[installer.id], work_start: e.target.value },
                                  }))}
                                />
                              </div>
                              <div>
                                <label className="text-slate-500 text-xs mb-1 block">Fim</label>
                                <input
                                  type="time"
                                  className="input text-sm"
                                  value={cfg.work_end}
                                  onChange={(e) => setInstallerSchedules(prev => ({
                                    ...prev,
                                    [installer.id]: { ...prev[installer.id], work_end: e.target.value },
                                  }))}
                                />
                              </div>
                            </div>
                            <div>
                              <label className="text-slate-500 text-xs mb-2 block">Dias disponíveis</label>
                              <div className="flex gap-1.5 flex-wrap">
                                {WEEKDAY_LABELS.map((label, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => toggleWeekday(idx, installer.id)}
                                    className={`w-9 h-9 rounded-lg text-xs font-semibold border transition-all ${
                                      cfg.allowed_weekdays.includes(idx)
                                        ? 'bg-emerald-600/80 text-white border-emerald-500/50'
                                        : 'bg-surface-700 text-slate-600 border-surface-600 hover:border-surface-500'
                                    }`}
                                  >
                                    {label}
                                  </button>
                                ))}
                              </div>
                            </div>
                            <div className="flex justify-end">
                              <button
                                onClick={() => handleSaveInstallerSchedule(installer.id)}
                                disabled={savingInstaller === installer.id}
                                className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5"
                              >
                                {savingInstaller === installer.id
                                  ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                  : <Save className="w-3.5 h-3.5" />
                                }
                                Salvar
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </Section>
            </>
          )}

          {tab === 'fluxo_bot' && (
            <>
              <div className="card p-5">
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="w-7 h-7 bg-brand-500/15 rounded-lg flex items-center justify-center text-brand-400">
                    <Bot className="w-4 h-4" />
                  </div>
                  <h3 className="text-white font-semibold text-sm">Mensagens do fluxo por domínio</h3>
                </div>
                <p className="text-slate-500 text-xs">
                  Configure as mensagens que o bot envia em cada domínio. Campos em branco utilizam os textos padrão do sistema.
                </p>
              </div>

              {flowConfigs.length === 0 ? (
                <div className="card p-12 text-center">
                  <div className="w-12 h-12 bg-surface-700 rounded-2xl flex items-center justify-center mx-auto mb-3">
                    <Bot className="w-6 h-6 text-slate-500" />
                  </div>
                  <p className="text-slate-500 text-sm">Carregando configurações do fluxo...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {flowConfigs.map(config => {
                    const isOpen = expandedDomain === config.key
                    const msgs = flowForms[config.key] ?? config.messages
                    return (
                      <div key={config.key} className="card overflow-hidden">
                        <button
                          onClick={() => setExpandedDomain(isOpen ? null : config.key)}
                          className="w-full flex items-center gap-3 p-4 hover:bg-surface-700/30 transition-colors"
                        >
                          <div className="flex-1 flex items-center gap-3 min-w-0 text-left">
                            <span className="text-white font-medium text-sm">{config.display_name}</span>
                            {config.is_customized && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-400 border border-brand-500/20 shrink-0">
                                Customizado
                              </span>
                            )}
                          </div>
                          {isOpen
                            ? <ChevronUp className="w-4 h-4 text-slate-500 shrink-0" />
                            : <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
                          }
                        </button>

                        {isOpen && (
                          <div className="px-4 pb-4 pt-2 border-t border-surface-700 space-y-4">
                            <div>
                              <label className="text-slate-400 text-xs font-medium mb-1.5 block">
                                Mensagem de boas-vindas
                              </label>
                              <textarea
                                className="input min-h-[80px] resize-none text-sm"
                                placeholder={config.messages.greeting || 'Texto padrão do sistema...'}
                                value={msgs.greeting}
                                onChange={(e) => setFlowForms(prev => ({
                                  ...prev,
                                  [config.key]: { ...prev[config.key], greeting: e.target.value },
                                }))}
                              />
                            </div>
                            <div>
                              <label className="text-slate-400 text-xs font-medium mb-1.5 block">
                                Mensagem de fallback (não entendeu)
                              </label>
                              <textarea
                                className="input min-h-[60px] resize-none text-sm"
                                placeholder={config.messages.fallback || 'Texto padrão do sistema...'}
                                value={msgs.fallback}
                                onChange={(e) => setFlowForms(prev => ({
                                  ...prev,
                                  [config.key]: { ...prev[config.key], fallback: e.target.value },
                                }))}
                              />
                            </div>
                            <div>
                              <label className="text-slate-400 text-xs font-medium mb-1.5 block">Tom da conversa</label>
                              <div className="relative">
                                <select
                                  className="input appearance-none pr-8 text-sm"
                                  value={msgs.tone}
                                  onChange={(e) => setFlowForms(prev => ({
                                    ...prev,
                                    [config.key]: { ...prev[config.key], tone: e.target.value },
                                  }))}
                                >
                                  {TONE_OPTIONS.map(t => (
                                    <option key={t} value={t} className="capitalize">{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                                  ))}
                                </select>
                                <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                              </div>
                            </div>
                            <div className="flex items-center justify-between pt-1">
                              <button
                                onClick={() => setFlowForms(prev => ({
                                  ...prev,
                                  [config.key]: { greeting: '', fallback: '', tone: config.messages.tone },
                                }))}
                                className="flex items-center gap-1.5 text-slate-500 hover:text-slate-300 text-xs transition-colors"
                              >
                                <RotateCcw className="w-3.5 h-3.5" />
                                Restaurar padrão
                              </button>
                              <button
                                onClick={() => handleSaveDomainFlow(config.key)}
                                disabled={savingDomain === config.key}
                                className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5"
                              >
                                {savingDomain === config.key
                                  ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                  : <Save className="w-3.5 h-3.5" />
                                }
                                Salvar mensagens
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {tab === 'garantia' && (
            <>
              <div className="card p-5">
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="w-7 h-7 bg-emerald-500/15 rounded-lg flex items-center justify-center text-emerald-400">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <h3 className="text-white font-semibold text-sm">Configuração da Garantia</h3>
                </div>
                <p className="text-slate-500 text-xs">
                  Defina o modelo padrão de garantia emitido após a conclusão de cada atendimento.
                  Nome e endereço do cliente são preenchidos automaticamente.
                </p>
              </div>

              <Section title="Texto da Garantia" icon={<ShieldCheck className="w-4 h-4" />}>
                <Field label="Descrição do serviço" hint="Descreva o serviço prestado conforme aparecerá no certificado.">
                  <textarea
                    className="input min-h-[80px] resize-none text-sm"
                    placeholder="Ex: Instalação profissional de película de controle solar conforme especificações acordadas."
                    value={warrantyForm.service_description}
                    onChange={e => setWarrantyForm(f => ({ ...f, service_description: e.target.value }))}
                  />
                </Field>

                <Field label="Prazo de garantia" hint="Período de cobertura. Ex: 12 meses, 2 anos.">
                  <input
                    className="input text-sm"
                    placeholder="12 meses"
                    value={warrantyForm.warranty_period}
                    onChange={e => setWarrantyForm(f => ({ ...f, warranty_period: e.target.value }))}
                  />
                </Field>

                <Field label="O que a garantia cobre" hint="Descreva os defeitos e situações cobertas pela garantia.">
                  <textarea
                    className="input min-h-[80px] resize-none text-sm"
                    placeholder="Ex: Defeitos de instalação, descolamento e bolhas originadas do serviço prestado. Não cobre danos por terceiros ou uso inadequado."
                    value={warrantyForm.warranty_covers}
                    onChange={e => setWarrantyForm(f => ({ ...f, warranty_covers: e.target.value }))}
                  />
                </Field>

                <Field label="Notas adicionais" hint="Texto complementar opcional (condições especiais, instruções de uso etc.).">
                  <textarea
                    className="input min-h-[60px] resize-none text-sm"
                    placeholder="Opcional..."
                    value={warrantyForm.additional_notes}
                    onChange={e => setWarrantyForm(f => ({ ...f, additional_notes: e.target.value }))}
                  />
                </Field>

                <Field label="Assinatura / Rodapé" hint="Nome ou assinatura final da empresa que aparece no rodapé do certificado.">
                  <input
                    className="input text-sm"
                    placeholder="Ex: Equipe AlphaSync — www.alphasync.app"
                    value={warrantyForm.signature}
                    onChange={e => setWarrantyForm(f => ({ ...f, signature: e.target.value }))}
                  />
                </Field>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleSaveWarranty}
                    disabled={savingWarranty}
                    className="btn-primary flex items-center gap-2 px-5"
                  >
                    {savingWarranty
                      ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      : <Save className="w-4 h-4" />
                    }
                    Salvar garantia
                  </button>
                </div>
              </Section>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
