import { useEffect, useState } from 'react'
import { CalendarDays, Clock, MapPin, User } from 'lucide-react'
import api from '../api/client'

interface Appointment {
  id: number
  client_id: number
  address_raw: string | null
  start_at: string
  end_at: string
  status: string
  service_type: string | null
  notes: string | null
  assigned_installer_id: number | null
}

const statusLabel: Record<string, string> = {
  scheduled: 'Agendado',
  in_progress: 'Em andamento',
  completed: 'Concluído',
  rescheduled: 'Reagendado',
  cancelled: 'Cancelado',
}

const statusColor: Record<string, string> = {
  scheduled: 'bg-blue-600/20 text-blue-400',
  in_progress: 'bg-amber-600/20 text-amber-400',
  completed: 'bg-emerald-600/20 text-emerald-400',
  rescheduled: 'bg-orange-600/20 text-orange-400',
  cancelled: 'bg-red-600/20 text-red-400',
}

export default function Schedule() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Appointment[]>('/appointments')
      .then(r => setAppointments(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-6 border-b border-surface-700">
        <h1 className="text-xl font-bold text-white">Agenda</h1>
        <p className="text-slate-400 text-sm mt-1">Agendamentos da empresa</p>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="w-7 h-7 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : appointments.length === 0 ? (
          <div className="card p-8 text-center">
            <CalendarDays className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-300 text-sm font-medium">Nenhum agendamento encontrado</p>
            <p className="text-slate-500 text-xs mt-1">Os agendamentos aparecerão aqui quando criados.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {appointments.map(a => (
              <div key={a.id} className="card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor[a.status] ?? 'bg-slate-700 text-slate-400'}`}>
                        {statusLabel[a.status] ?? a.status}
                      </span>
                      {a.service_type && (
                        <span className="text-xs text-slate-500">{a.service_type}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-300 text-sm mb-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span>
                        {new Date(a.start_at).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}
                        {' – '}
                        {new Date(a.end_at).toLocaleTimeString('pt-BR', { timeStyle: 'short' })}
                      </span>
                    </div>
                    {a.address_raw && (
                      <div className="flex items-center gap-1.5 text-slate-400 text-xs">
                        <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="truncate">{a.address_raw}</span>
                      </div>
                    )}
                  </div>
                  <div className="text-slate-500 text-xs shrink-0">#{a.id}</div>
                </div>
                {a.notes && (
                  <p className="mt-2 text-slate-500 text-xs border-t border-surface-700 pt-2">{a.notes}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
