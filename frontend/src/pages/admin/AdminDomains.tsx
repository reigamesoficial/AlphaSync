import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Globe, RefreshCw, Pencil, X, Save, AlertCircle, CheckCircle2,
  Code2, MessageSquare, Layers, DollarSign, Settings2, Plus, Trash2,
  ToggleLeft, ToggleRight, Info, ShieldAlert,
} from 'lucide-react'
import {
  listDomains, getDomain, updateDomain, syncDomains,
  type DomainDefinitionListItem, type DomainDefinitionDetail,
} from '../../api/admin'

// ─── Helpers ─────────────────────────────────────────────────────────────────

type ConfigJson = Record<string, unknown>
type Tab = 'general' | 'flow' | 'services' | 'pricing' | 'onboarding' | 'json'

function getStr(obj: ConfigJson | undefined, key: string, fallback = ''): string {
  return typeof obj?.[key] === 'string' ? (obj[key] as string) : fallback
}
function getNum(obj: ConfigJson | undefined, key: string, fallback = 0): number {
  return typeof obj?.[key] === 'number' ? (obj[key] as number) : fallback
}
function getArr(obj: ConfigJson | undefined, key: string): string[] {
  const v = obj?.[key]
  return Array.isArray(v) ? (v as string[]) : []
}
function getObj(obj: ConfigJson | undefined, key: string): ConfigJson {
  const v = obj?.[key]
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as ConfigJson) : {}
}

function serialize(v: unknown): string { return JSON.stringify(v, null, 2) }

// ─── Sub-components ───────────────────────────────────────────────────────────

interface StatCardProps { label: string; value: number; color: string }
function StatCard({ label, value, color }: StatCardProps) {
  return (
    <div className="card p-4 flex flex-col gap-1">
      <span className="text-slate-400 text-xs font-medium">{label}</span>
      <span className={`text-2xl font-bold ${color}`}>{value}</span>
    </div>
  )
}

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

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">{children}</p>
}

function FieldRow({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="label flex items-center gap-1.5">
        {label}
        {hint && <span title={hint}><Info className="w-3 h-3 text-slate-600 cursor-help" /></span>}
      </label>
      {children}
    </div>
  )
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative inline-flex w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none ${
        checked ? 'bg-emerald-500' : 'bg-surface-600'
      }`}
    >
      <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${
        checked ? 'translate-x-5' : 'translate-x-0'
      }`} />
    </button>
  )
}

function TagList({ items, onAdd, onRemove }: {
  items: string[]
  onAdd: (v: string) => void
  onRemove: (i: number) => void
}) {
  const [input, setInput] = useState('')

  function submit() {
    const val = input.trim()
    if (val && !items.includes(val)) { onAdd(val); setInput('') }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 bg-violet-500/15 text-violet-300 text-xs font-medium px-2.5 py-1 rounded-full"
          >
            {item}
            <button onClick={() => onRemove(i)} className="text-violet-400 hover:text-red-400 transition-colors ml-0.5">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        {items.length === 0 && <span className="text-slate-600 text-xs italic">Nenhum item adicionado.</span>}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
          className="input flex-1 text-sm"
          placeholder="Novo item…"
        />
        <button onClick={submit} className="btn-secondary text-sm px-3">
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

function JsonEditor({ value, onChange }: {
  value: ConfigJson
  onChange: (v: ConfigJson) => void
}) {
  const [raw, setRaw] = useState(() => serialize(value))
  const [error, setError] = useState('')

  useEffect(() => { setRaw(serialize(value)) }, [value])

  function handleChange(text: string) {
    setRaw(text)
    try {
      const parsed = JSON.parse(text)
      setError('')
      onChange(parsed)
    } catch { setError('JSON inválido — verifique a sintaxe.') }
  }

  return (
    <div className="space-y-2">
      <textarea
        value={raw}
        onChange={e => handleChange(e.target.value)}
        rows={22}
        spellCheck={false}
        className="w-full bg-surface-900 border border-surface-600 rounded-lg p-3 text-xs text-slate-300 font-mono resize-y focus:outline-none focus:border-violet-500 transition-colors"
      />
      {error ? (
        <p className="text-xs text-red-400 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{error}</p>
      ) : (
        <p className="text-xs text-slate-600">{raw.split('\n').length} linhas · {new Blob([raw]).size} bytes</p>
      )}
    </div>
  )
}

// ─── Drawer tabs ──────────────────────────────────────────────────────────────

function TabGeneral({ detail, form, setForm }: {
  detail: DomainDefinitionDetail
  form: { display_name: string; description: string; icon: string; is_active: boolean }
  setForm: React.Dispatch<React.SetStateAction<typeof form>>
}) {
  return (
    <div className="space-y-5">
      <SectionLabel>Identificação</SectionLabel>

      <div className="grid grid-cols-[1fr_80px] gap-3">
        <FieldRow label="Nome de exibição">
          <input
            type="text"
            value={form.display_name}
            onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))}
            className="input w-full"
            placeholder="Ex: Redes de Proteção"
          />
        </FieldRow>
        <FieldRow label="Ícone" hint="Emoji representando o domínio">
          <input
            type="text"
            value={form.icon}
            onChange={e => setForm(f => ({ ...f, icon: e.target.value }))}
            className="input w-full text-center text-xl"
            placeholder="🔧"
            maxLength={4}
          />
        </FieldRow>
      </div>

      <FieldRow label="Descrição curta">
        <textarea
          value={form.description}
          onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          className="input w-full resize-none"
          rows={2}
          placeholder="Breve descrição do domínio de serviço"
        />
      </FieldRow>

      <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-surface-900 border border-surface-600">
        <div>
          <p className="text-white text-sm font-medium">Domínio ativo</p>
          <p className="text-slate-500 text-xs">Empresas podem usar este domínio</p>
        </div>
        <Toggle checked={form.is_active} onChange={v => setForm(f => ({ ...f, is_active: v }))} />
      </div>

      <div className="rounded-lg bg-surface-900 border border-surface-600 divide-y divide-surface-700 text-xs">
        <div className="flex justify-between items-center px-4 py-2.5">
          <span className="text-slate-500">Key (identificador)</span>
          <span className="font-mono text-slate-300 bg-surface-700 px-2 py-0.5 rounded">{detail.key}</span>
        </div>
        <div className="flex justify-between items-center px-4 py-2.5">
          <span className="text-slate-500">Tipo</span>
          <BuiltinBadge builtin={detail.is_builtin} />
        </div>
        <div className="flex justify-between items-center px-4 py-2.5">
          <span className="text-slate-500">Criado em</span>
          <span className="text-slate-400">{new Date(detail.created_at).toLocaleDateString('pt-BR')}</span>
        </div>
        <div className="flex justify-between items-center px-4 py-2.5">
          <span className="text-slate-500">Atualizado em</span>
          <span className="text-slate-400">{new Date(detail.updated_at).toLocaleDateString('pt-BR')}</span>
        </div>
      </div>
    </div>
  )
}

function TabFlow({ config, onChange }: {
  config: ConfigJson
  onChange: (c: ConfigJson) => void
}) {
  const bot = getObj(config, 'bot')
  const labels = getObj(config, 'labels')

  function setBot(key: string, value: string) {
    onChange({ ...config, bot: { ...bot, [key]: value } })
  }
  function setLabel(key: string, value: string) {
    onChange({ ...config, labels: { ...labels, [key]: value } })
  }

  const TONES = ['amigável', 'profissional', 'técnico', 'objetivo', 'formal']

  return (
    <div className="space-y-5">
      <SectionLabel>Mensagens do Bot</SectionLabel>

      <FieldRow label="Mensagem inicial" hint="Primeira mensagem enviada ao cliente ao iniciar o atendimento">
        <textarea
          value={getStr(bot, 'greeting_message')}
          onChange={e => setBot('greeting_message', e.target.value)}
          className="input w-full resize-none"
          rows={3}
          placeholder="Olá! Bem-vindo(a) ao serviço de..."
        />
      </FieldRow>

      <FieldRow label="Mensagem de confirmação" hint="Enviada antes de gerar o orçamento">
        <textarea
          value={getStr(bot, 'confirm_message')}
          onChange={e => setBot('confirm_message', e.target.value)}
          className="input w-full resize-none"
          rows={2}
          placeholder="Perfeito! Confira os dados abaixo:"
        />
      </FieldRow>

      <FieldRow label="Mensagem de fallback" hint="Enviada quando o bot não entende a resposta">
        <textarea
          value={getStr(bot, 'fallback_message')}
          onChange={e => setBot('fallback_message', e.target.value)}
          className="input w-full resize-none"
          rows={2}
          placeholder="Não entendi. Pode repetir ou digitar *menu*?"
        />
      </FieldRow>

      <FieldRow label="Tom do assistente" hint="Define o perfil de comunicação do bot">
        <div className="flex flex-wrap gap-2">
          {TONES.map(tone => (
            <button
              key={tone}
              onClick={() => setBot('tone', tone)}
              className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-all ${
                getStr(bot, 'tone') === tone
                  ? 'bg-violet-500/20 border-violet-500/50 text-violet-300'
                  : 'bg-transparent border-surface-600 text-slate-400 hover:border-surface-500 hover:text-white'
              }`}
            >
              {tone}
            </button>
          ))}
        </div>
      </FieldRow>

      {Object.keys(labels).length > 0 && (
        <>
          <div className="border-t border-surface-700 pt-4">
            <SectionLabel>Labels do Formulário</SectionLabel>
            <div className="space-y-3">
              {Object.entries(labels).map(([k, v]) => (
                <div key={k} className="grid grid-cols-[120px_1fr] gap-2 items-center">
                  <span className="text-slate-500 text-xs font-mono bg-surface-900 px-2 py-1.5 rounded border border-surface-600 truncate">{k}</span>
                  <input
                    type="text"
                    value={typeof v === 'string' ? v : ''}
                    onChange={e => setLabel(k, e.target.value)}
                    className="input text-sm"
                    placeholder={`Label para "${k}"`}
                  />
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function TabServices({ config, onChange }: {
  config: ConfigJson
  onChange: (c: ConfigJson) => void
}) {
  const services = getArr(config, 'services')

  function setServices(list: string[]) {
    onChange({ ...config, services: list })
  }

  return (
    <div className="space-y-5">
      <SectionLabel>Serviços disponíveis</SectionLabel>
      <p className="text-xs text-slate-500 -mt-3">
        Lista de serviços oferecidos neste domínio. São usados como opções durante o fluxo do chatbot.
      </p>

      <TagList
        items={services}
        onAdd={v => setServices([...services, v])}
        onRemove={i => setServices(services.filter((_, idx) => idx !== i))}
      />

      {services.length > 0 && (
        <div className="rounded-lg bg-surface-900 border border-surface-600 divide-y divide-surface-700">
          {services.map((svc, i) => (
            <div key={i} className="flex items-center justify-between px-4 py-2.5 group">
              <div className="flex items-center gap-2.5">
                <span className="text-slate-600 text-xs font-mono w-5 text-right">{i + 1}.</span>
                <span className="text-slate-300 text-sm">{svc}</span>
              </div>
              <button
                onClick={() => setServices(services.filter((_, idx) => idx !== i))}
                className="text-slate-700 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function TabPricing({ config, onChange }: {
  config: ConfigJson
  onChange: (c: ConfigJson) => void
}) {
  const pricing = getObj(config, 'pricing_defaults')

  function setField(key: string, value: number) {
    onChange({ ...config, pricing_defaults: { ...pricing, [key]: value } })
  }

  const KNOWN: { key: string; label: string; hint: string }[] = [
    { key: 'minimum_order_value', label: 'Valor mínimo do pedido (R$)', hint: 'Menor valor aceito para gerar um orçamento' },
    { key: 'visit_fee', label: 'Taxa de visita técnica (R$)', hint: 'Cobrada pela visita, independente do serviço' },
    { key: 'default_price_per_m2', label: 'Preço padrão por m² (R$)', hint: 'Usado em domínios com cálculo por área' },
    { key: 'price_per_camera', label: 'Preço por câmera (R$)', hint: 'Específico para o domínio de câmeras de segurança' },
  ]

  const knownKeys = KNOWN.map(k => k.key)
  const extraEntries = Object.entries(pricing).filter(([k]) => !knownKeys.includes(k))

  return (
    <div className="space-y-5">
      <SectionLabel>Valores padrão de precificação</SectionLabel>
      <p className="text-xs text-slate-500 -mt-3">
        Estes valores são usados como ponto de partida ao criar novas empresas neste domínio.
        Cada empresa pode ter sua própria configuração de preços nas configurações da empresa.
      </p>

      <div className="space-y-3">
        {KNOWN.filter(f => Object.prototype.hasOwnProperty.call(pricing, f.key)).map(({ key, label, hint }) => (
          <FieldRow key={key} label={label} hint={hint}>
            <div className="flex items-center gap-2">
              <span className="text-slate-400 text-sm font-medium">R$</span>
              <input
                type="number"
                min={0}
                step={0.01}
                value={getNum(pricing, key)}
                onChange={e => setField(key, parseFloat(e.target.value) || 0)}
                className="input flex-1"
              />
            </div>
          </FieldRow>
        ))}
      </div>

      {extraEntries.length > 0 && (
        <div className="border-t border-surface-700 pt-4">
          <SectionLabel>Outros campos de pricing</SectionLabel>
          <div className="space-y-3">
            {extraEntries.map(([k, v]) => (
              <FieldRow key={k} label={k}>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={typeof v === 'number' ? v : 0}
                  onChange={e => setField(k, parseFloat(e.target.value) || 0)}
                  className="input w-full"
                />
              </FieldRow>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function TabOnboarding({ config, onChange }: {
  config: ConfigJson
  onChange: (c: ConfigJson) => void
}) {
  const od = getObj(config, 'onboarding_defaults')

  function setOd(key: string, value: unknown) {
    onChange({ ...config, onboarding_defaults: { ...od, [key]: value } })
  }

  const CURRENCIES = ['BRL', 'USD', 'EUR', 'ARS', 'CLP', 'MXN']
  const TIMEZONES = [
    'America/Sao_Paulo', 'America/Manaus', 'America/Belem',
    'America/Fortaleza', 'America/Recife', 'America/Bahia',
    'America/Cuiaba', 'America/Porto_Velho', 'America/Boa_Vista',
    'America/Rio_Branco', 'America/Noronha',
  ]

  return (
    <div className="space-y-5">
      <SectionLabel>Defaults para novas empresas</SectionLabel>
      <p className="text-xs text-slate-500 -mt-3">
        Quando uma empresa é criada com este domínio, estas configurações são aplicadas automaticamente
        às configurações da empresa. Cada empresa pode personalizar depois.
      </p>

      <div className="grid grid-cols-2 gap-3">
        <FieldRow label="Nome do bot" hint="Nome do assistente virtual exibido para os clientes">
          <input
            type="text"
            value={getStr(od, 'bot_name')}
            onChange={e => setOd('bot_name', e.target.value)}
            className="input w-full"
            placeholder="Ex: Assistente"
          />
        </FieldRow>
        <FieldRow label="Prefixo do orçamento" hint="Código que precede o número do orçamento, ex: ORC-001">
          <input
            type="text"
            value={getStr(od, 'quote_prefix')}
            onChange={e => setOd('quote_prefix', e.target.value.toUpperCase())}
            className="input w-full font-mono uppercase"
            placeholder="ORC"
            maxLength={6}
          />
        </FieldRow>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <FieldRow label="Moeda padrão">
          <select
            value={getStr(od, 'currency', 'BRL')}
            onChange={e => setOd('currency', e.target.value)}
            className="input w-full"
          >
            {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </FieldRow>
        <FieldRow label="Fuso horário">
          <select
            value={getStr(od, 'timezone', 'America/Sao_Paulo')}
            onChange={e => setOd('timezone', e.target.value)}
            className="input w-full"
          >
            {TIMEZONES.map(tz => (
              <option key={tz} value={tz}>{tz.replace('America/', '')}</option>
            ))}
          </select>
        </FieldRow>
      </div>

      {Object.keys(getObj(od, 'extra_settings')).length > 0 && (
        <div className="rounded-lg bg-surface-900 border border-surface-600 p-3">
          <p className="text-xs text-slate-500 mb-2">Extra settings (use a aba JSON Avançado para editar):</p>
          <pre className="text-xs text-slate-400 font-mono overflow-auto max-h-32">
            {serialize(getObj(od, 'extra_settings'))}
          </pre>
        </div>
      )}
    </div>
  )
}

function TabJson({ config, onChange }: {
  config: ConfigJson
  onChange: (c: ConfigJson) => void
}) {
  const [acknowledged, setAcknowledged] = useState(false)

  if (!acknowledged) {
    return (
      <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 p-5 space-y-4">
        <div className="flex gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-amber-300 font-semibold text-sm">Editor JSON avançado</p>
            <p className="text-amber-200/70 text-xs mt-1 leading-relaxed">
              Esta aba permite editar o <strong>config_json completo</strong> do domínio diretamente.
              Use somente se as abas guiadas não forem suficientes para o que você precisa.
            </p>
            <ul className="mt-2 space-y-1 text-xs text-amber-200/60 list-disc list-inside">
              <li>JSON inválido não será salvo</li>
              <li>Mudanças aqui substituem toda a configuração</li>
              <li>Prefira as abas Fluxo, Serviços, Pricing e Onboarding</li>
            </ul>
          </div>
        </div>
        <button
          onClick={() => setAcknowledged(true)}
          className="w-full py-2 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300 text-sm font-medium hover:bg-amber-500/30 transition-colors"
        >
          Entendi — abrir editor JSON
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
        Edições aqui afetam todo o config_json. As abas guiadas refletem estas mudanças após salvar.
      </div>
      <JsonEditor value={config} onChange={onChange} />
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'general',    label: 'Geral',       icon: Settings2 },
  { id: 'flow',       label: 'Fluxo',       icon: MessageSquare },
  { id: 'services',   label: 'Serviços',    icon: Layers },
  { id: 'pricing',    label: 'Pricing',     icon: DollarSign },
  { id: 'onboarding', label: 'Onboarding',  icon: Globe },
  { id: 'json',       label: 'JSON',        icon: Code2 },
]

interface Toast { msg: string; type: 'success' | 'error' }

export default function AdminDomains() {
  const [domains, setDomains] = useState<DomainDefinitionListItem[]>([])
  const [loading, setLoading]   = useState(true)
  const [syncing, setSyncing]   = useState(false)

  const [editKey, setEditKey]         = useState<string | null>(null)
  const [detail, setDetail]           = useState<DomainDefinitionDetail | null>(null)
  const [detailLoading, setDL]        = useState(false)
  const [tab, setTab]                 = useState<Tab>('general')

  // form state
  const [form, setForm] = useState({ display_name: '', description: '', icon: '', is_active: true })
  const [config, setConfig] = useState<ConfigJson>({})

  // dirty tracking
  const originalRef = useRef<string>('')
  function isDirty() {
    return JSON.stringify({ ...form, config }) !== originalRef.current
  }

  const [saving, setSaving]   = useState(false)
  const [toast, setToast]     = useState<Toast | null>(null)

  function showToast(msg: string, type: 'success' | 'error') {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setDomains(await listDomains())
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
      showToast('Erro ao sincronizar', 'error')
    } finally {
      setSyncing(false)
    }
  }

  async function openEdit(key: string) {
    setEditKey(key)
    setTab('general')
    setDL(true)
    try {
      const d = await getDomain(key)
      setDetail(d)
      const f = { display_name: d.display_name, description: d.description ?? '', icon: d.icon ?? '', is_active: d.is_active }
      setForm(f)
      setConfig(d.config_json)
      originalRef.current = JSON.stringify({ ...f, config: d.config_json })
    } catch {
      showToast('Erro ao carregar domínio', 'error')
      setEditKey(null)
    } finally {
      setDL(false)
    }
  }

  function closeEdit() {
    setEditKey(null)
    setDetail(null)
  }

  async function handleSave() {
    if (!detail || !isDirty()) return
    setSaving(true)
    try {
      await updateDomain(detail.key, {
        display_name: form.display_name,
        description: form.description || null,
        icon: form.icon || null,
        is_active: form.is_active,
        config_json: config,
      })
      showToast('Domínio atualizado com sucesso', 'success')
      await load()
      closeEdit()
    } catch {
      showToast('Erro ao salvar domínio', 'error')
    } finally {
      setSaving(false)
    }
  }

  // stats
  const total    = domains.length
  const active   = domains.filter(d => d.is_active).length
  const builtin  = domains.filter(d => d.is_builtin).length
  const custom   = domains.filter(d => !d.is_builtin).length

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl text-sm font-medium backdrop-blur ${
          toast.type === 'success'
            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            : 'bg-red-500/20 text-red-300 border border-red-500/30'
        }`}>
          {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      {/* Page header */}
      <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur border-b border-surface-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-violet-600/20 rounded-lg flex items-center justify-center">
            <Globe className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-base">Domínios de Serviço</h1>
            <p className="text-slate-500 text-xs">Configure os domínios disponíveis na plataforma</p>
          </div>
        </div>
        <button onClick={handleSync} disabled={syncing} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Sincronizando…' : 'Sincronizar'}
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Stat cards */}
        {!loading && (
          <div className="grid grid-cols-4 gap-4">
            <StatCard label="Total"   value={total}   color="text-white" />
            <StatCard label="Ativos"  value={active}  color="text-emerald-400" />
            <StatCard label="Builtin" value={builtin} color="text-violet-400" />
            <StatCard label="Custom"  value={custom}  color="text-amber-400" />
          </div>
        )}

        {/* Domain list */}
        {loading ? (
          <div className="flex items-center justify-center h-40 text-slate-500 text-sm">Carregando…</div>
        ) : domains.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-slate-500 text-sm gap-3">
            <Globe className="w-8 h-8 opacity-30" />
            <p>Nenhum domínio cadastrado.</p>
            <button onClick={handleSync} disabled={syncing} className="btn-secondary text-sm">Sincronizar agora</button>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-600 bg-surface-900/50">
                  <th className="text-left text-slate-400 font-medium text-xs px-4 py-3">Domínio</th>
                  <th className="text-left text-slate-400 font-medium text-xs px-4 py-3 hidden lg:table-cell">Descrição</th>
                  <th className="text-left text-slate-400 font-medium text-xs px-4 py-3 hidden md:table-cell">Tipo</th>
                  <th className="text-left text-slate-400 font-medium text-xs px-4 py-3">Status</th>
                  <th className="text-right text-slate-400 font-medium text-xs px-4 py-3">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-700">
                {domains.map(d => (
                  <tr key={d.key} className="hover:bg-surface-800/40 transition-colors group">
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-lg shrink-0">
                          {d.icon ?? '🔧'}
                        </div>
                        <div>
                          <p className="text-white font-medium">{d.display_name}</p>
                          <p className="text-slate-500 text-xs font-mono">{d.key}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 hidden lg:table-cell">
                      <p className="text-slate-400 text-xs max-w-xs truncate">{d.description ?? '—'}</p>
                    </td>
                    <td className="px-4 py-3.5 hidden md:table-cell">
                      <BuiltinBadge builtin={d.is_builtin} />
                    </td>
                    <td className="px-4 py-3.5">
                      <ActivePill active={d.is_active} />
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <button
                        onClick={() => openEdit(d.key)}
                        className="inline-flex items-center gap-1.5 text-xs text-violet-400 hover:text-violet-200 transition-colors font-medium bg-violet-500/10 hover:bg-violet-500/20 px-3 py-1.5 rounded-lg border border-violet-500/20 hover:border-violet-500/40"
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
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={closeEdit} />
          <div className="relative ml-auto w-full max-w-2xl bg-surface-800 border-l border-surface-600 flex flex-col h-full shadow-2xl">

            {/* Drawer header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-600 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-violet-600/15 border border-violet-500/25 flex items-center justify-center text-2xl">
                  {form.icon || detail?.icon || '🔧'}
                </div>
                <div>
                  <h2 className="text-white font-semibold text-sm">{form.display_name || editKey}</h2>
                  <p className="text-slate-500 text-xs font-mono">{editKey}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {isDirty() && (
                  <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/25 px-2.5 py-1 rounded-full font-medium">
                    Alterações pendentes
                  </span>
                )}
                <button onClick={closeEdit} className="text-slate-400 hover:text-white transition-colors p-1">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-surface-600 shrink-0 overflow-x-auto scrollbar-hide">
              {TABS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  className={`flex items-center gap-1.5 px-4 py-3 text-xs font-medium border-b-2 whitespace-nowrap transition-colors ${
                    tab === id
                      ? 'border-violet-500 text-violet-400'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </button>
              ))}
            </div>

            {/* Drawer body */}
            <div className="flex-1 overflow-y-auto p-5">
              {detailLoading ? (
                <div className="flex items-center justify-center h-32 text-slate-500 text-sm">Carregando…</div>
              ) : detail ? (
                <>
                  {tab === 'general'    && <TabGeneral    detail={detail} form={form} setForm={setForm} />}
                  {tab === 'flow'       && <TabFlow       config={config} onChange={setConfig} />}
                  {tab === 'services'   && <TabServices   config={config} onChange={setConfig} />}
                  {tab === 'pricing'    && <TabPricing    config={config} onChange={setConfig} />}
                  {tab === 'onboarding' && <TabOnboarding config={config} onChange={setConfig} />}
                  {tab === 'json'       && <TabJson       config={config} onChange={setConfig} />}
                </>
              ) : null}
            </div>

            {/* Drawer footer */}
            <div className="px-5 py-4 border-t border-surface-600 shrink-0 flex items-center justify-between">
              <p className="text-xs text-slate-600">
                {isDirty() ? 'Você tem alterações não salvas.' : 'Nenhuma alteração.'}
              </p>
              <div className="flex gap-3">
                <button onClick={closeEdit} className="btn-secondary text-sm">Cancelar</button>
                <button
                  onClick={handleSave}
                  disabled={saving || detailLoading || !isDirty()}
                  className={`flex items-center gap-2 text-sm px-4 py-2 rounded-lg font-medium transition-all ${
                    isDirty() && !saving
                      ? 'btn-primary'
                      : 'bg-surface-700 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Salvando…' : 'Salvar alterações'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
