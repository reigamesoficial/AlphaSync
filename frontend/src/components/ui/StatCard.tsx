import { ReactNode } from 'react'

interface Props {
  label: string
  value: string | number
  sub?: string
  icon?: ReactNode
  trend?: 'up' | 'down' | 'neutral'
  accent?: string
}

export default function StatCard({ label, value, sub, icon, accent = 'brand' }: Props) {
  const accents: Record<string, string> = {
    brand:   'bg-brand-500/10 text-brand-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    amber:   'bg-amber-500/10 text-amber-400',
    sky:     'bg-sky-500/10 text-sky-400',
    violet:  'bg-violet-500/10 text-violet-400',
  }

  return (
    <div className="card p-5 flex items-start gap-4">
      {icon && (
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${accents[accent] ?? accents.brand}`}>
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-slate-400 text-sm font-medium truncate">{label}</p>
        <p className="text-white text-2xl font-semibold mt-0.5">{value}</p>
        {sub && <p className="text-slate-500 text-xs mt-1">{sub}</p>}
      </div>
    </div>
  )
}
