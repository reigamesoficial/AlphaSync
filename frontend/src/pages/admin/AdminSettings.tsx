import { Settings } from 'lucide-react'

export default function AdminSettings() {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">Configurações SaaS</h1>
        <p className="text-slate-400 text-sm mt-1">Configurações globais da plataforma AlphaSync</p>
      </div>
      <div className="card p-8 text-center">
        <Settings className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-300 text-sm font-medium">Em breve</p>
        <p className="text-slate-500 text-xs mt-1">Configurações globais serão implementadas aqui.</p>
      </div>
    </div>
  )
}
