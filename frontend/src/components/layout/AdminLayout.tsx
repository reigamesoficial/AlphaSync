import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  Building2,
  Users,
  BarChart3,
  Settings,
  Zap,
  ChevronRight,
  LogOut,
  Globe,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const nav = [
  { to: '/admin/companies', label: 'Empresas',      icon: Building2 },
  { to: '/admin/users',     label: 'Usuários',      icon: Users },
  { to: '/admin/domains',   label: 'Domínios',      icon: Globe },
  { to: '/admin/metrics',   label: 'Métricas',      icon: BarChart3 },
  { to: '/admin/settings',  label: 'Config. SaaS', icon: Settings },
]

export default function AdminLayout() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const initials = user?.name
    ? user.name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
    : 'M'

  return (
    <div className="flex h-screen overflow-hidden bg-surface-900">
      <aside className="w-60 shrink-0 bg-surface-800 border-r border-surface-600 flex flex-col h-full">
        <div className="h-16 flex items-center px-5 border-b border-surface-600">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-violet-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <span className="font-semibold text-white text-sm tracking-wide">AlphaSync</span>
              <p className="text-[10px] text-violet-400 leading-none">Painel Master</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
          <p className="text-slate-600 text-[10px] font-semibold uppercase tracking-widest px-2 pb-2">
            Plataforma
          </p>
          {nav.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to || location.pathname.startsWith(to + '/')
            return (
              <NavLink
                key={to}
                to={to}
                className={`group flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                  active
                    ? 'bg-violet-600/20 text-violet-400'
                    : 'text-slate-400 hover:text-white hover:bg-surface-700'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-violet-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <span className="flex-1">{label}</span>
                {active && <ChevronRight className="w-3 h-3 text-violet-500 opacity-70" />}
              </NavLink>
            )
          })}
        </nav>

        <div className="p-3 border-t border-surface-600">
          <div className="card p-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-violet-600/30 flex items-center justify-center text-violet-400 text-xs font-bold shrink-0">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-white text-xs font-medium truncate">{user?.name ?? '—'}</p>
                <p className="text-slate-500 text-[10px] truncate">Master Admin</p>
              </div>
              <button
                onClick={logout}
                className="text-slate-500 hover:text-red-400 transition-colors"
                title="Sair"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}
