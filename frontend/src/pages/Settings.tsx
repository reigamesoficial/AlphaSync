import { useEffect, useState } from 'react'
import {
  Settings as SettingsIcon, Save, Bot, Palette, Globe,
  AlertCircle, CheckCircle, Shield, Eye, EyeOff, Plus, X,
} from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { PageSpinner } from '../components/ui/Spinner'
import { getCompanySettings, updateCompanySettings } from '../api/company'
import { getPNSettings, updatePNSettings } from '../api/measures'
import type { CompanySettings, PNSettings } from '../types'

const TIMEZONES = ['America/Sao_Paulo', 'America/Manaus', 'America/Belem', 'America/Fortaleza', 'America/Recife']
const CURRENCIES = ['BRL', 'USD', 'EUR']
type Tab = 'empresa' | 'protection_network'

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

interface FieldProps { label: string; children: React.ReactNode }
function Field({ label, children }: FieldProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-start py-3 border-b border-surface-700 last:border-0">
      <label className="text-slate-400 text-sm font-medium pt-1.5">{label}</label>
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

export default function Settings() {
  const [tab, setTab] = useState<Tab>('empresa')
  const [settings, setSettings] = useState<CompanySettings | null>(null)
  const [pnSettings, setPnSettings] = useState<PNSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [form, setForm] = useState<Partial<CompanySettings>>({})
  const [pnForm, setPnForm] = useState<Partial<PNSettings>>({})

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
        })
        setPnForm({ ...pn })
      })
      .catch(() => setToast({ type: 'error', msg: 'Erro ao carregar configurações.' }))
      .finally(() => setLoading(false))
  }, [])

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

  function field(key: keyof CompanySettings) {
    return {
      value: (form[key] as string) ?? '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
        setForm((prev) => ({ ...prev, [key]: e.target.value })),
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

          <div className="flex gap-1 p-1 bg-surface-800 border border-surface-600 rounded-xl w-fit">
            {([
              { key: 'empresa', label: 'Empresa' },
              { key: 'protection_network', label: 'Protection Network' },
            ] as { key: Tab; label: string }[]).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
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
                <Field label="Token de verificação WhatsApp">
                  <input className="input" type="password" placeholder="••••••••" {...field('whatsapp_verify_token')} />
                </Field>
                {settings?.extra_settings?.bot && (
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
            </>
          )}
        </div>
      </main>
    </div>
  )
}
