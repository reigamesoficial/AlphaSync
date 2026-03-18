import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { CalendarDays, Zap, LogOut } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const NAV = [
  { to: '/installer', label: 'Minha Agenda', icon: CalendarDays },
]

export default function InstallerLayout() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const initials = user?.name
    ? user.name.split(' ').slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()
    : 'I'

  return (
    <div className="flex h-screen overflow-hidden bg-surface-900">
      {/* Sidebar — visível apenas desktop (md+) */}
      <aside className="hidden md:flex w-60 shrink-0 bg-surface-800 border-r border-surface-600 flex-col h-full">
        <div className="h-16 flex items-center px-5 border-b border-surface-600">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <span className="font-semibold text-white text-sm tracking-wide">AlphaSync</span>
              <p className="text-[10px] text-brand-400 leading-none">Instalador</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
          <p className="text-slate-600 text-[10px] font-semibold uppercase tracking-widest px-2 pb-2">
            Meu Painel
          </p>
          {NAV.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to || location.pathname.startsWith(to + '/')
            return (
              <NavLink
                key={to}
                to={to}
                className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  active
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-slate-400 hover:text-white hover:bg-surface-700'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <span className="flex-1">{label}</span>
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
                <p className="text-slate-500 text-[10px] truncate">Instalador</p>
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

      {/* Área principal */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header mobile — aparece apenas em telas pequenas */}
        <header className="md:hidden flex items-center justify-between h-14 px-4 bg-surface-800 border-b border-surface-600 shrink-0 safe-top">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-semibold text-white text-sm">AlphaSync</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-full bg-brand-600/30 flex items-center justify-center text-brand-400 text-xs font-bold">
              {initials}
            </div>
            <button
              onClick={logout}
              className="text-slate-500 hover:text-red-400 transition-colors p-1"
              title="Sair"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Conteúdo da página */}
        <div className="flex-1 overflow-hidden">
          <Outlet />
        </div>

        {/* Bottom Nav — mobile only */}
        <nav className="md:hidden flex border-t border-surface-600 bg-surface-800 safe-bottom shrink-0">
          {NAV.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to || location.pathname.startsWith(to + '/')
            return (
              <NavLink
                key={to}
                to={to}
                className={`flex-1 flex flex-col items-center justify-center py-2.5 gap-1 text-[10px] font-medium transition-colors ${
                  active ? 'text-brand-400' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-brand-400' : ''}`} />
                {label}
              </NavLink>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
