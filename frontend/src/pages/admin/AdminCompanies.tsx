import { useEffect, useState } from 'react'
import { Building2, CheckCircle, XCircle, Search } from 'lucide-react'
import api from '../../api/client'

interface Company {
  id: number
  slug: string
  name: string
  service_domain: string
  plan_name: string | null
  is_active: boolean
  status: string
  support_email: string | null
  created_at: string
}

export default function AdminCompanies() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  function load() {
    setLoading(true)
    const params = search ? { search } : {}
    api.get<Company[]>('/admin/companies', { params })
      .then(r => setCompanies(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    load()
  }

  const domainLabel: Record<string, string> = {
    protection_network: 'Proteção Solar',
    generic: 'Genérico',
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Empresas</h1>
          <p className="text-slate-400 text-sm mt-1">{companies.length} empresa{companies.length !== 1 ? 's' : ''} cadastrada{companies.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="mb-4 flex gap-2">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            className="w-full bg-surface-700 border border-surface-600 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
            placeholder="Buscar empresa..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <button type="submit" className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white text-sm rounded-lg transition-colors">
          Buscar
        </button>
      </form>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-7 h-7 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : companies.length === 0 ? (
        <div className="card p-8 text-center">
          <Building2 className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Nenhuma empresa encontrada.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-600">
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Empresa</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Domínio</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Plano</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Criada em</th>
              </tr>
            </thead>
            <tbody>
              {companies.map(c => (
                <tr key={c.id} className="border-b border-surface-700 hover:bg-surface-700/50 transition-colors">
                  <td className="px-4 py-3">
                    <p className="text-white font-medium">{c.name}</p>
                    <p className="text-slate-500 text-xs">{c.slug}</p>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{domainLabel[c.service_domain] ?? c.service_domain}</td>
                  <td className="px-4 py-3 text-slate-300">{c.plan_name ?? '—'}</td>
                  <td className="px-4 py-3">
                    {c.is_active ? (
                      <span className="flex items-center gap-1 text-emerald-400 text-xs">
                        <CheckCircle className="w-3.5 h-3.5" /> Ativa
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-400 text-xs">
                        <XCircle className="w-3.5 h-3.5" /> Inativa
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {new Date(c.created_at).toLocaleDateString('pt-BR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
