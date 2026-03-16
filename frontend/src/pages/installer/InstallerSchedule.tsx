import { useEffect, useState } from 'react'
import { CalendarDays, Clock, MapPin, CheckCircle, PlayCircle, XCircle, RotateCcw } from 'lucide-react'
import api from '../../api/client'

interface Appointment {
  id: number
  client_id: number
  address_raw: string | null
  start_at: string
  end_at: string
  status: string
  service_type: string | null
  notes: string | null
  installers: string[] | null
}

const statusLabel: Record<string, string> = {
  scheduled: 'Agendado',
  in_progress: 'Em andamento',
  completed: 'Concluído',
  rescheduled: 'Reagendado',
  cancelled: 'Cancelado',
}

const statusColor: Record<string, string> = {
  scheduled: 'bg-blue-600/20 text-blue-400 border-blue-600/30',
  in_progress: 'bg-amber-600/20 text-amber-400 border-amber-600/30',
  completed: 'bg-emerald-600/20 text-emerald-400 border-emerald-600/30',
  rescheduled: 'bg-orange-600/20 text-orange-400 border-orange-600/30',
  cancelled: 'bg-red-600/20 text-red-400 border-red-600/30',
}

const nextActions: Record<string, { status: string; label: string; icon: typeof CheckCircle }[]> = {
  scheduled: [{ status: 'in_progress', label: 'Iniciar atendimento', icon: PlayCircle }],
  in_progress: [{ status: 'completed', label: 'Marcar como concluído', icon: CheckCircle }],
  completed: [],
  rescheduled: [{ status: 'in_progress', label: 'Iniciar atendimento', icon: PlayCircle }],
  cancelled: [],
}

export default function InstallerSchedule() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<number | null>(null)

  function load() {
    setLoading(true)
    api.get<Appointment[]>('/installer/appointments')
      .then(r => setAppointments(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function updateStatus(id: number, status: string) {
    setUpdating(id)
    try {
      await api.patch(`/installer/appointments/${id}/status`, { status })
      load()
    } catch {
      // silent
    } finally {
      setUpdating(null)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-6 border-b border-surface-700">
        <h1 className="text-xl font-bold text-white">Minha Agenda</h1>
        <p className="text-slate-400 text-sm mt-1">Seus atendimentos agendados</p>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="w-7 h-7 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : appointments.length === 0 ? (
          <div className="card p-8 text-center">
            <CalendarDays className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-300 text-sm font-medium">Nenhum atendimento agendado</p>
            <p className="text-slate-500 text-xs mt-1">Seus próximos atendimentos aparecerão aqui.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {appointments.map(a => {
              const actions = nextActions[a.status] ?? []
              return (
                <div key={a.id} className={`card border p-4 ${statusColor[a.status] ?? 'border-surface-600'}`}>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${statusColor[a.status] ?? 'bg-slate-700 text-slate-400 border-slate-600'}`}>
                      {statusLabel[a.status] ?? a.status}
                    </span>
                    {a.service_type && (
                      <span className="text-xs text-slate-500">{a.service_type}</span>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center gap-1.5 text-white text-sm">
                      <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>
                        {new Date(a.start_at).toLocaleString('pt-BR', { dateStyle: 'full', timeStyle: 'short' })}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-300 text-xs">
                      <Clock className="w-3.5 h-3.5 text-transparent shrink-0" />
                      <span>
                        {new Date(a.start_at).toLocaleTimeString('pt-BR', { timeStyle: 'short' })}
                        {' – '}
                        {new Date(a.end_at).toLocaleTimeString('pt-BR', { timeStyle: 'short' })}
                      </span>
                    </div>
                    {a.address_raw && (
                      <div className="flex items-center gap-1.5 text-slate-300 text-sm">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>{a.address_raw}</span>
                      </div>
                    )}
                  </div>

                  {a.notes && (
                    <p className="mt-3 text-slate-400 text-xs border-t border-surface-700 pt-2">{a.notes}</p>
                  )}

                  {actions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-surface-700 flex gap-2">
                      {actions.map(({ status, label, icon: Icon }) => (
                        <button
                          key={status}
                          onClick={() => updateStatus(a.id, status)}
                          disabled={updating === a.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs rounded-lg transition-colors"
                        >
                          <Icon className="w-3.5 h-3.5" />
                          {label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
