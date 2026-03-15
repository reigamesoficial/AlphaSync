const variants: Record<string, string> = {
  open:      'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30',
  bot:       'bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/30',
  assumed:   'bg-violet-500/15 text-violet-400 ring-1 ring-violet-500/30',
  closed:    'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/30',
  archived:  'bg-slate-700/30 text-slate-500 ring-1 ring-slate-600/30',
  lead:      'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30',
  qualified: 'bg-sky-500/15 text-sky-400 ring-1 ring-sky-500/30',
  customer:  'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30',
  inactive:  'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/30',
  draft:     'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30',
  confirmed: 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30',
  cancelled: 'bg-red-500/15 text-red-400 ring-1 ring-red-500/30',
  done:      'bg-sky-500/15 text-sky-400 ring-1 ring-sky-500/30',
  expired:   'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/30',
  whatsapp:  'bg-green-500/15 text-green-400 ring-1 ring-green-500/30',
  manual:    'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/30',
  import:    'bg-violet-500/15 text-violet-400 ring-1 ring-violet-500/30',
}

const labels: Record<string, string> = {
  open: 'Aberta', bot: 'Bot', assumed: 'Assumida', closed: 'Fechada', archived: 'Arquivada',
  lead: 'Lead', qualified: 'Qualificado', customer: 'Cliente', inactive: 'Inativo',
  draft: 'Rascunho', confirmed: 'Confirmado', cancelled: 'Cancelado', done: 'Concluído', expired: 'Expirado',
  whatsapp: 'WhatsApp', manual: 'Manual', import: 'Importado',
  in: 'Entrada', out: 'Saída',
}

export default function Badge({ value, className = '' }: { value: string; className?: string }) {
  const cls = variants[value] ?? 'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/30'
  const label = labels[value] ?? value
  return (
    <span className={`badge ${cls} ${className}`}>
      {label}
    </span>
  )
}
