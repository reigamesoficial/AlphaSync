import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  FileText,
  Settings,
  Zap,
  ChevronRight,
  Ruler,
  CalendarDays,
  UserCog,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const adminNav = [
  { to: '/dashboard',       label: 'Dashboard',     icon: LayoutDashboard },
  { to: '/conversations',   label: 'Conversas',     icon: MessageSquare },
  { to: '/clients',         label: 'Clientes',      icon: Users },
  { to: '/quotes',          label: 'Orçamentos',    icon: FileText },
  { to: '/measures',        label: 'Medidas',       icon: Ruler },
  { to: '/schedule',        label: 'Agenda',        icon: CalendarDays },
  { to: '/company-users',   label: 'Usuários',      icon: UserCog },
  { to: '/settings',        label: 'Configurações', icon: Settings },
]

const sellerNav = [
  { to: '/dashboard',     label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/conversations', label: 'Conversas',   icon: MessageSquare },
  { to: '/clients',       label: 'Clientes',    icon: Users },
  { to: '/quotes',        label: 'Orçamentos',  icon: FileText },
  { to: '/measures',      label: 'Medidas',     icon: Ruler },
  { to: '/schedule',      label: 'Agenda',      icon: CalendarDays },
]

const roleLabels: Record<string, string> = {
  master_admin: 'Master Admin',
  company_admin: 'Administrador',
  seller: 'Vendedor',
  installer: 'Instalador',
  viewer: 'Visualizador',
}

export default function Sidebar() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const nav = user?.role === 'seller' ? sellerNav : adminNav

  const initials = user?.name
    ? user.name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
    : '?'

  return (
    <aside className="w-60 shrink-0 bg-surface-800 border-r border-surface-600 flex flex-col h-full">
      <div className="h-16 flex items-center px-5 border-b border-surface-600">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <span className="font-semibold text-white text-sm tracking-wide">AlphaSync</span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        <p className="text-slate-600 text-[10px] font-semibold uppercase tracking-widest px-2 pb-2">
          Menu
        </p>
        {nav.map(({ to, label, icon: Icon }) => {
          const active = location.pathname === to || location.pathname.startsWith(to + '/')
          return (
            <NavLink
              key={to}
              to={to}
              className={`group flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                active
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-slate-400 hover:text-white hover:bg-surface-700'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight className="w-3 h-3 text-brand-500 opacity-70" />}
            </NavLink>
          )
        })}
      </nav>

      <div className="p-3 border-t border-surface-600">
        <div className="card p-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-brand-600/30 flex items-center justify-center text-brand-400 text-xs font-bold shrink-0">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-white text-xs font-medium truncate">{user?.name ?? '—'}</p>
              <p className="text-slate-500 text-[10px] truncate">{roleLabels[user?.role ?? ''] ?? user?.role}</p>
            </div>
            <button
              onClick={logout}
              className="text-slate-600 hover:text-slate-400 transition-colors text-[10px] shrink-0"
              title="Sair"
            >
              Sair
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}
