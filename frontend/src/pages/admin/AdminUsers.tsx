import { useEffect, useState } from 'react'
import { Users, Search } from 'lucide-react'
import api from '../../api/client'

interface AdminUser {
  id: number
  name: string
  email: string
  role: string
  company_id: number | null
  is_active: boolean
  created_at: string
}

const roleLabel: Record<string, string> = {
  master_admin: 'Master Admin',
  company_admin: 'Administrador',
  seller: 'Vendedor',
  installer: 'Instalador',
  viewer: 'Visualizador',
}

export default function AdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<AdminUser[]>('/admin/users')
      .then(r => setUsers(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">Usuários</h1>
        <p className="text-slate-400 text-sm mt-1">{users.length} usuário{users.length !== 1 ? 's' : ''} cadastrado{users.length !== 1 ? 's' : ''}</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-7 h-7 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : users.length === 0 ? (
        <div className="card p-8 text-center">
          <Users className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Nenhum usuário encontrado.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-600">
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Nome</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">E-mail</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Papel</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Empresa ID</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-b border-surface-700 hover:bg-surface-700/50 transition-colors">
                  <td className="px-4 py-3 text-white font-medium">{u.name}</td>
                  <td className="px-4 py-3 text-slate-300">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-violet-600/20 text-violet-400">
                      {roleLabel[u.role] ?? u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{u.company_id ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs ${u.is_active ? 'text-emerald-400' : 'text-red-400'}`}>
                      {u.is_active ? 'Ativo' : 'Inativo'}
                    </span>
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
