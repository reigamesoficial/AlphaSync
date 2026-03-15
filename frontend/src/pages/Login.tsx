import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Zap, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('admin@alphasync.app')
  const [password, setPassword] = useState('changeme123')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Erro ao fazer login. Verifique suas credenciais.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-900 flex">
      <div className="hidden lg:flex flex-1 items-center justify-center bg-surface-800 border-r border-surface-600 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-surface-800 to-surface-800" />
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-brand-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-48 h-48 bg-violet-600/10 rounded-full blur-3xl" />
        <div className="relative z-10 text-center max-w-sm px-8">
          <div className="w-16 h-16 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-brand-600/30">
            <Zap className="w-8 h-8 text-white" strokeWidth={2} />
          </div>
          <h2 className="text-white text-2xl font-bold mb-3">AlphaSync</h2>
          <p className="text-slate-400 text-sm leading-relaxed">
            Plataforma SaaS para empresas de serviço com automação por WhatsApp e gestão completa de clientes.
          </p>
          <div className="mt-10 grid grid-cols-2 gap-4">
            {[
              { label: 'Conversas', value: 'WhatsApp' },
              { label: 'Orçamentos', value: 'Automático' },
              { label: 'Clientes', value: 'Multiempresa' },
              { label: 'Dashboard', value: 'Tempo real' },
            ].map((f) => (
              <div key={f.label} className="bg-surface-700/50 rounded-xl p-3 text-left">
                <p className="text-brand-400 text-xs font-semibold">{f.value}</p>
                <p className="text-slate-300 text-sm font-medium mt-0.5">{f.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-white">AlphaSync</span>
          </div>

          <div className="mb-8">
            <h1 className="text-white text-2xl font-bold">Bem-vindo de volta</h1>
            <p className="text-slate-400 mt-1 text-sm">Entre com suas credenciais para acessar o painel.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-start gap-2.5 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">E-mail</label>
              <input
                type="email"
                autoComplete="email"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className="input pr-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button type="submit" className="btn-primary w-full py-2.5 mt-2" disabled={loading}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Entrando...
                </span>
              ) : (
                'Entrar'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
