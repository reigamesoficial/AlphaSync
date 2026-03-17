import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Users, MessageSquare, FileText, Settings,
  Zap, Ruler, CalendarDays, UserCog, BarChart3, GitBranch,
  Sun, Moon, LogOut,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useTheme } from '../../context/ThemeContext'

const adminSections = [
  {
    label: 'Operacional',
    items: [
      { to: '/dashboard',     label: 'Dashboard',    icon: LayoutDashboard },
      { to: '/conversations', label: 'Conversas',    icon: MessageSquare },
      { to: '/clients',       label: 'Clientes',     icon: Users },
      { to: '/quotes',        label: 'Orçamentos',   icon: FileText },
    ],
  },
  {
    label: 'Análise',
    items: [
      { to: '/financial', label: 'Financeiro',  icon: BarChart3 },
      { to: '/crm',       label: 'CRM / Funil', icon: GitBranch },
    ],
  },
  {
    label: 'Campo',
    items: [
      { to: '/measures', label: 'Medidas', icon: Ruler },
      { to: '/schedule', label: 'Agenda',  icon: CalendarDays },
    ],
  },
  {
    label: 'Gestão',
    items: [
      { to: '/company-users', label: 'Usuários',      icon: UserCog },
      { to: '/settings',      label: 'Configurações', icon: Settings },
    ],
  },
]

const sellerSections = [
  {
    label: 'Operacional',
    items: [
      { to: '/dashboard',     label: 'Dashboard',   icon: LayoutDashboard },
      { to: '/conversations', label: 'Conversas',   icon: MessageSquare },
      { to: '/clients',       label: 'Clientes',    icon: Users },
      { to: '/quotes',        label: 'Orçamentos',  icon: FileText },
    ],
  },
  {
    label: 'Análise',
    items: [
      { to: '/financial', label: 'Financeiro',  icon: BarChart3 },
      { to: '/crm',       label: 'CRM / Funil', icon: GitBranch },
    ],
  },
  {
    label: 'Campo',
    items: [
      { to: '/measures', label: 'Medidas', icon: Ruler },
      { to: '/schedule', label: 'Agenda',  icon: CalendarDays },
    ],
  },
]

const roleLabels: Record<string, string> = {
  master_admin:  'Master Admin',
  company_admin: 'Administrador',
  seller:        'Vendedor',
  installer:     'Instalador',
  viewer:        'Visualizador',
}

const roleAccent: Record<string, string> = {
  company_admin: 'bg-brand-400',
  seller:        'bg-emerald-400',
  master_admin:  'bg-amber-400',
}

interface SidebarProps {
  onClose?: () => void
}

export default function Sidebar({ onClose }: SidebarProps) {
  const location = useLocation()
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  const sections = user?.role === 'seller' ? sellerSections : adminSections
  const initials = user?.name
    ? user.name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
    : '?'

  return (
    <aside className="w-60 shrink-0 bg-surface-800 border-r border-surface-600 flex flex-col h-full">

      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-surface-600 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center shadow-lg shadow-brand-600/30">
            <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <p className="font-bold text-white text-sm tracking-wide leading-tight">AlphaSync</p>
            <p className="text-[9px] text-slate-500 font-medium uppercase tracking-widest">Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-1 px-3">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="section-label">{section.label}</p>
            {section.items.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to || location.pathname.startsWith(to + '/')
              return (
                <NavLink
                  key={to}
                  to={to}
                  onClick={onClose}
                  className={`group flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 mb-0.5 ${
                    active
                      ? 'bg-brand-600/15 text-brand-400 border border-brand-500/25'
                      : 'text-slate-400 hover:text-white hover:bg-surface-700 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 transition-colors ${active ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                  <span className="flex-1 truncate">{label}</span>
                  {active && <span className="w-1.5 h-1.5 rounded-full bg-brand-400 shrink-0" />}
                </NavLink>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="shrink-0 border-t border-surface-600">
        {/* Theme toggle */}
        <div className="px-4 py-2.5 flex items-center gap-3 border-b border-surface-600">
          {theme === 'dark' ? <Moon className="w-3.5 h-3.5 text-slate-500" /> : <Sun className="w-3.5 h-3.5 text-amber-400" />}
          <span className="text-xs text-slate-400 flex-1">Tema {theme === 'dark' ? 'escuro' : 'claro'}</span>
          <button
            onClick={toggleTheme}
            className={`w-9 h-5 rounded-full relative transition-colors duration-200 ${theme === 'light' ? 'bg-brand-500' : 'bg-surface-500'}`}
            title={theme === 'dark' ? 'Mudar para claro' : 'Mudar para escuro'}
          >
            <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${theme === 'light' ? 'translate-x-4' : 'translate-x-0.5'}`} />
          </button>
        </div>

        {/* User profile */}
        <div className="p-3">
          <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-surface-700 transition-colors cursor-default">
            <div className="relative shrink-0">
              <div className="w-8 h-8 rounded-full bg-brand-600/20 flex items-center justify-center text-brand-400 text-xs font-bold">
                {initials}
              </div>
              <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-surface-800 ${roleAccent[user?.role ?? ''] ?? 'bg-slate-500'}`} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-white text-xs font-semibold truncate leading-tight">{user?.name ?? '—'}</p>
              <p className="text-slate-500 text-[10px] truncate">{roleLabels[user?.role ?? ''] ?? user?.role}</p>
            </div>
            <button
              onClick={logout}
              className="text-slate-600 hover:text-red-400 hover:bg-red-500/10 rounded-md p-1 transition-colors shrink-0"
              title="Sair"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}
