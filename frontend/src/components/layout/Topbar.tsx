import { LogOut, Bell } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useNavigate } from 'react-router-dom'

interface Props {
  title: string
  subtitle?: string
}

export default function Topbar({ title, subtitle }: Props) {
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-16 bg-surface-800 border-b border-surface-600 flex items-center justify-between px-6 shrink-0">
      <div>
        <h1 className="text-white font-semibold text-base">{title}</h1>
        {subtitle && <p className="text-slate-500 text-xs mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">
        <button className="relative w-8 h-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-white hover:bg-surface-700 transition-colors">
          <Bell className="w-4 h-4" />
        </button>
        <div className="h-5 w-px bg-surface-500 mx-1" />
        <div className="flex items-center gap-2">
          <div className="text-right hidden sm:block">
            <p className="text-white text-xs font-medium">{user?.name}</p>
            <p className="text-slate-500 text-[10px]">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="Sair"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
