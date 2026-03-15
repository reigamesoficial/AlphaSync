import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Save, Bot, Palette, Globe, AlertCircle, CheckCircle } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { PageSpinner } from '../components/ui/Spinner'
import { getCompanySettings, updateCompanySettings } from '../api/company'
import type { CompanySettings } from '../types'

const TIMEZONES = ['America/Sao_Paulo', 'America/Manaus', 'America/Belem', 'America/Fortaleza', 'America/Recife']
const CURRENCIES = ['BRL', 'USD', 'EUR']

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

export default function Settings() {
  const [settings, setSettings] = useState<CompanySettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [form, setForm] = useState<Partial<CompanySettings>>({})

  useEffect(() => {
    getCompanySettings()
      .then((s) => {
        setSettings(s)
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
      })
      .catch(() => setToast({ type: 'error', msg: 'Erro ao carregar configurações.' }))
      .finally(() => setLoading(false))
  }, [])

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
      setToast({ type: 'success', msg: 'Configurações salvas com sucesso!' })
    } catch {
      setToast({ type: 'error', msg: 'Erro ao salvar. Tente novamente.' })
    } finally {
      setSaving(false)
      setTimeout(() => setToast(null), 4000)
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
                Regras de precificação são configuradas via domínio. Edição avançada disponível em breve.
              </p>
            </Section>
          )}

          <div className="flex justify-end pt-2">
            <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2 px-6">
              {saving ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Salvar configurações
                </>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
