import { Bell, ChevronRight } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

interface Props {
  title: string
  subtitle?: string
  breadcrumb?: string
  action?: React.ReactNode
}

export default function Topbar({ title, subtitle, breadcrumb, action }: Props) {
  const { user } = useAuth()

  return (
    <header className="h-16 bg-surface-800 border-b border-surface-600 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-2">
        {breadcrumb && (
          <>
            <span className="text-slate-500 text-sm">{breadcrumb}</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
          </>
        )}
        <div>
          <h1 className="text-white font-semibold text-base leading-tight">{title}</h1>
          {subtitle && <p className="text-slate-500 text-xs mt-0.5">{subtitle}</p>}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {action && <div className="mr-1">{action}</div>}
        <button className="relative w-8 h-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-white hover:bg-surface-700 transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-brand-400 rounded-full" />
        </button>
        <div className="h-5 w-px bg-surface-600 mx-1" />
        <div className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-surface-700 transition-colors">
          <div className="w-7 h-7 rounded-full bg-brand-600/20 flex items-center justify-center text-brand-400 text-xs font-bold shrink-0">
            {user?.name?.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase() ?? '?'}
          </div>
          <div className="hidden sm:block text-right">
            <p className="text-white text-xs font-medium leading-tight">{user?.name}</p>
            <p className="text-slate-500 text-[10px]">{user?.email}</p>
          </div>
        </div>
      </div>
    </header>
  )
}
