import { useEffect, useState, useCallback } from 'react'
import {
  MapPin, Plus, ChevronRight, Pencil, Trash2,
  LayoutGrid, Building2, Ruler, X, Search, AlertCircle, Layers, Info,
} from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { PageSpinner } from '../components/ui/Spinner'
import {
  getMeasureStats, listAddresses, createAddress, updateAddress, deleteAddress,
  createPlant, updatePlant, deletePlant, createItem, updateItem, deleteItem,
} from '../api/measures'
import type { AddressWithHierarchy, MeasureStats, Plant, MeasureItem } from '../types'

const BR_STATES = [
  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
  'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
]

type ModalType = 'address' | 'plant' | 'item' | null

interface Toast { type: 'success' | 'error'; msg: string }

function StatCard({ label, value, icon, sub }: { label: string; value: number; icon: React.ReactNode; sub?: string }) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className="w-11 h-11 bg-brand-500/15 rounded-xl flex items-center justify-center text-brand-400 shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-white tabular-nums">{value}</p>
        <p className="text-slate-400 text-sm">{label}</p>
        {sub && <p className="text-slate-600 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface-800 rounded-2xl border border-surface-600 w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b border-surface-600">
          <h3 className="text-white font-semibold">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors p-1 rounded-lg hover:bg-surface-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

function Drawer({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface-800 border-l border-surface-600 w-full max-w-md h-full flex flex-col shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b border-surface-600 shrink-0">
          <h3 className="text-white font-semibold">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors p-1 rounded-lg hover:bg-surface-700">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
      </div>
    </div>
  )
}

interface AddrForm { raw_address: string; city: string; state: string; zipcode: string; notes: string }
interface PlantForm { name: string; sort_order: string }
interface ItemForm { label: string; width_m: string; height_m: string; quantity: string; notes: string; plant_id: string }

const emptyAddrForm: AddrForm = { raw_address: '', city: '', state: '', zipcode: '', notes: '' }
const emptyPlantForm: PlantForm = { name: '', sort_order: '0' }
const emptyItemForm: ItemForm = { label: '', width_m: '', height_m: '', quantity: '1', notes: '', plant_id: '' }

function totalArea(items: MeasureItem[]): number {
  return items.reduce((s, it) => s + Number(it.area_m2 ?? 0), 0)
}

export default function Measures() {
  const [stats, setStats] = useState<MeasureStats>({ total_addresses: 0, total_plants: 0, total_items: 0 })
  const [addresses, setAddresses] = useState<AddressWithHierarchy[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [search, setSearch] = useState('')
  const [filterCity, setFilterCity] = useState('')
  const [filterState, setFilterState] = useState('')
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [toast, setToast] = useState<Toast | null>(null)

  const [modal, setModal] = useState<ModalType>(null)
  const [editingAddr, setEditingAddr] = useState<AddressWithHierarchy | null>(null)
  const [editingPlant, setEditingPlant] = useState<Plant | null>(null)
  const [editingItem, setEditingItem] = useState<MeasureItem | null>(null)
  const [targetAddressId, setTargetAddressId] = useState<number | null>(null)

  const [addrForm, setAddrForm] = useState<AddrForm>(emptyAddrForm)
  const [plantForm, setPlantForm] = useState<PlantForm>(emptyPlantForm)
  const [itemForm, setItemForm] = useState<ItemForm>(emptyItemForm)

  const showToast = (type: Toast['type'], msg: string) => {
    setToast({ type, msg })
    setTimeout(() => setToast(null), 4000)
  }

  const loadData = useCallback(async () => {
    try {
      const [s, a] = await Promise.all([
        getMeasureStats(),
        listAddresses({ search: search || undefined, city: filterCity || undefined, state: filterState || undefined }),
      ])
      setStats(s)
      setAddresses(a)
    } catch {
      showToast('error', 'Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [search, filterCity, filterState])

  useEffect(() => { loadData() }, [loadData])

  function toggleExpand(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function openNewAddress() { setEditingAddr(null); setAddrForm(emptyAddrForm); setModal('address') }
  function openEditAddress(entry: AddressWithHierarchy) {
    setEditingAddr(entry)
    setAddrForm({ raw_address: entry.address.raw_address, city: entry.address.city ?? '', state: entry.address.state ?? '', zipcode: entry.address.zipcode ?? '', notes: entry.address.notes ?? '' })
    setModal('address')
  }

  function openNewPlant(addressId: number) { setEditingPlant(null); setTargetAddressId(addressId); setPlantForm(emptyPlantForm); setModal('plant') }
  function openEditPlant(plant: Plant) {
    setEditingPlant(plant)
    setTargetAddressId(plant.address_catalog_id)
    setPlantForm({ name: plant.name, sort_order: String(plant.sort_order) })
    setModal('plant')
  }

  function openNewItem(addressId: number, plantId?: number) {
    setEditingItem(null)
    setTargetAddressId(addressId)
    setItemForm({ ...emptyItemForm, plant_id: plantId ? String(plantId) : '' })
    setModal('item')
  }
  function openEditItem(item: MeasureItem) {
    setEditingItem(item)
    setTargetAddressId(item.address_catalog_id)
    setItemForm({ label: item.label, width_m: String(item.width_m), height_m: String(item.height_m), quantity: String(item.quantity), notes: item.notes ?? '', plant_id: item.plant_id ? String(item.plant_id) : '' })
    setModal('item')
  }

  function closeModal() { setModal(null); setEditingAddr(null); setEditingPlant(null); setEditingItem(null); setTargetAddressId(null) }

  async function handleSaveAddress() {
    setSaving(true)
    try {
      const payload = { raw_address: addrForm.raw_address.trim(), city: addrForm.city.trim() || undefined, state: addrForm.state.trim() || undefined, zipcode: addrForm.zipcode.trim() || undefined, notes: addrForm.notes.trim() || undefined }
      if (editingAddr) { await updateAddress(editingAddr.address.id, payload); showToast('success', 'Endereço atualizado.') }
      else { const created = await createAddress(payload); setExpanded((prev) => new Set([...prev, created.address.id])); showToast('success', 'Endereço criado.') }
      closeModal(); await loadData()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      showToast('error', msg || 'Erro ao salvar endereço.')
    } finally { setSaving(false) }
  }

  async function handleDeleteAddress(id: number) {
    if (!confirm('Excluir este endereço e todos os seus dados?')) return
    try { await deleteAddress(id); showToast('success', 'Endereço removido.'); await loadData() }
    catch { showToast('error', 'Erro ao excluir endereço.') }
  }

  async function handleSavePlant() {
    if (!targetAddressId) return
    setSaving(true)
    try {
      if (editingPlant) { await updatePlant(editingPlant.id, { name: plantForm.name.trim(), sort_order: Number(plantForm.sort_order) }); showToast('success', 'Planta atualizada.') }
      else { await createPlant({ address_catalog_id: targetAddressId, name: plantForm.name.trim(), sort_order: Number(plantForm.sort_order) }); showToast('success', 'Planta criada.') }
      closeModal(); await loadData()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      showToast('error', msg || 'Erro ao salvar planta.')
    } finally { setSaving(false) }
  }

  async function handleDeletePlant(id: number) {
    if (!confirm('Excluir esta planta e todas as suas medidas?')) return
    try { await deletePlant(id); showToast('success', 'Planta removida.'); await loadData() }
    catch { showToast('error', 'Erro ao excluir planta.') }
  }

  async function handleSaveItem() {
    if (!targetAddressId) return
    setSaving(true)
    try {
      const payload = { address_catalog_id: targetAddressId, plant_id: itemForm.plant_id ? Number(itemForm.plant_id) : null, label: itemForm.label.trim(), width_m: parseFloat(itemForm.width_m), height_m: parseFloat(itemForm.height_m), quantity: parseInt(itemForm.quantity), notes: itemForm.notes.trim() || undefined }
      if (editingItem) { await updateItem(editingItem.id, payload); showToast('success', 'Medida atualizada.') }
      else { await createItem(payload); showToast('success', 'Medida criada.') }
      closeModal(); await loadData()
    } catch { showToast('error', 'Erro ao salvar medida.') }
    finally { setSaving(false) }
  }

  async function handleDeleteItem(id: number) {
    if (!confirm('Excluir esta medida?')) return
    try { await deleteItem(id); showToast('success', 'Medida removida.'); await loadData() }
    catch { showToast('error', 'Erro ao excluir medida.') }
  }

  const targetEntry = targetAddressId ? addresses.find(e => e.address.id === targetAddressId) : null
  const areaCalc = itemForm.width_m && itemForm.height_m && itemForm.quantity
    ? (parseFloat(itemForm.width_m || '0') * parseFloat(itemForm.height_m || '0') * parseInt(itemForm.quantity || '1')).toFixed(2)
    : null

  if (loading) {
    return (
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar title="Catálogo de Medidas" />
        <div className="flex-1 flex items-center justify-center"><PageSpinner /></div>
      </div>
    )
  }

  const totalAreaAll = addresses.reduce((s, e) => {
    const plantItems = e.plants.flatMap(pw => pw.items)
    return s + totalArea([...plantItems, ...e.direct_items])
  }, 0)

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title="Catálogo de Medidas" subtitle="Endereços, plantas e medidas dos clientes" />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl space-y-5">

          {toast && (
            <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-medium ${
              toast.type === 'success'
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/10 border border-red-500/20 text-red-400'
            }`}>
              <AlertCircle className="w-4 h-4 shrink-0" />
              {toast.msg}
            </div>
          )}

          <div className="grid grid-cols-4 gap-4">
            <StatCard label="Endereços" value={stats.total_addresses} icon={<MapPin className="w-5 h-5" />} />
            <StatCard label="Plantas" value={stats.total_plants} icon={<Building2 className="w-5 h-5" />} />
            <StatCard label="Medidas" value={stats.total_items} icon={<Ruler className="w-5 h-5" />} />
            <StatCard label="Área total" value={Math.round(totalAreaAll)} sub="m² cadastrados" icon={<LayoutGrid className="w-5 h-5" />} />
          </div>

          <div className="card p-4 flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-surface-700 rounded-lg px-3 py-2 flex-1 min-w-[200px]">
              <Search className="w-4 h-4 text-slate-500 shrink-0" />
              <input
                className="bg-transparent text-white placeholder-slate-500 text-sm outline-none w-full"
                placeholder="Buscar por endereço..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <input className="input w-40" placeholder="Cidade" value={filterCity} onChange={(e) => setFilterCity(e.target.value)} />
            <select className="input w-32" value={filterState} onChange={(e) => setFilterState(e.target.value)}>
              <option value="">Estado</option>
              {BR_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <button onClick={openNewAddress} className="btn-primary flex items-center gap-2 whitespace-nowrap ml-auto">
              <Plus className="w-4 h-4" />
              Novo endereço
            </button>
          </div>

          {addresses.length === 0 ? (
            <div className="card p-16 text-center">
              <div className="w-14 h-14 bg-surface-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MapPin className="w-7 h-7 text-slate-500" />
              </div>
              <p className="text-white font-medium mb-1">Nenhum endereço cadastrado</p>
              <p className="text-slate-500 text-sm">Clique em "Novo endereço" para começar a cadastrar o catálogo de medidas.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {addresses.map((entry) => {
                const isOpen = expanded.has(entry.address.id)
                const plantCount = entry.plants.length
                const allItems = [...entry.plants.flatMap(pw => pw.items), ...entry.direct_items]
                const itemCount = allItems.length
                const area = totalArea(allItems)

                return (
                  <div key={entry.address.id} className="card overflow-hidden">
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={() => toggleExpand(entry.address.id)}
                      onKeyDown={(e) => e.key === 'Enter' && toggleExpand(entry.address.id)}
                      className="w-full flex items-center gap-3 p-4 hover:bg-surface-700/50 transition-colors cursor-pointer select-none"
                    >
                      <div className={`transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}>
                        <ChevronRight className="w-4 h-4 text-slate-500" />
                      </div>
                      <MapPin className="w-4 h-4 text-brand-400 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium text-sm truncate">{entry.address.raw_address}</p>
                        {(entry.address.city || entry.address.state) && (
                          <p className="text-slate-500 text-xs">
                            {[entry.address.city, entry.address.state].filter(Boolean).join(' · ')}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-3 mr-1">
                          <span className="text-xs text-slate-500">
                            {plantCount} planta{plantCount !== 1 ? 's' : ''}
                          </span>
                          <span className="text-xs text-slate-500">
                            {itemCount} medida{itemCount !== 1 ? 's' : ''}
                          </span>
                          {area > 0 && (
                            <span className="text-xs text-brand-400 font-semibold tabular-nums">
                              {area.toFixed(1)} m²
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => openEditAddress(entry)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-surface-600 transition-colors"
                          title="Editar endereço"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteAddress(entry.address.id)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Excluir endereço"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {isOpen && (
                      <div className="border-t border-surface-600 bg-surface-900/30">
                        <div className="p-4 space-y-3">

                          {entry.plants.map((pw) => {
                            const plantArea = totalArea(pw.items)
                            return (
                              <div key={pw.plant.id} className="bg-surface-800 rounded-xl border border-surface-600 overflow-hidden">
                                <div className="flex items-center gap-2 px-4 py-2.5 border-b border-surface-600 bg-surface-750">
                                  <Layers className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                                  <span className="text-white text-sm font-medium flex-1">{pw.plant.name}</span>
                                  {plantArea > 0 && (
                                    <span className="text-xs text-brand-400 font-semibold tabular-nums mr-2">
                                      {plantArea.toFixed(1)} m²
                                    </span>
                                  )}
                                  <span className="text-xs text-slate-600 mr-1">
                                    {pw.items.length} medida{pw.items.length !== 1 ? 's' : ''}
                                  </span>
                                  <button
                                    onClick={() => openNewItem(entry.address.id, pw.plant.id)}
                                    className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 transition-colors px-2 py-1 rounded-lg hover:bg-brand-500/10"
                                  >
                                    <Plus className="w-3 h-3" /> Medida
                                  </button>
                                  <button
                                    onClick={() => openEditPlant(pw.plant)}
                                    className="p-1.5 text-slate-500 hover:text-white hover:bg-surface-600 rounded-lg transition-colors"
                                    title="Editar planta"
                                  >
                                    <Pencil className="w-3 h-3" />
                                  </button>
                                  <button
                                    onClick={() => handleDeletePlant(pw.plant.id)}
                                    className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                    title="Excluir planta"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                </div>
                                {pw.items.length === 0 ? (
                                  <div className="flex items-center gap-2 px-4 py-3 text-slate-600 text-xs">
                                    <Info className="w-3.5 h-3.5 shrink-0" />
                                    Nenhuma medida cadastrada nesta planta.
                                  </div>
                                ) : (
                                  <ItemTable items={pw.items} onEdit={openEditItem} onDelete={handleDeleteItem} />
                                )}
                              </div>
                            )
                          })}

                          {entry.direct_items.length > 0 && (
                            <div className="bg-surface-800 rounded-xl border border-surface-600 overflow-hidden">
                              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-surface-600">
                                <Ruler className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                                <span className="text-slate-400 text-sm font-medium flex-1">Medidas sem planta</span>
                                {totalArea(entry.direct_items) > 0 && (
                                  <span className="text-xs text-slate-400 font-semibold tabular-nums">
                                    {totalArea(entry.direct_items).toFixed(1)} m²
                                  </span>
                                )}
                              </div>
                              <ItemTable items={entry.direct_items} onEdit={openEditItem} onDelete={handleDeleteItem} />
                            </div>
                          )}

                          <div className="flex gap-2 pt-1">
                            <button
                              onClick={() => openNewPlant(entry.address.id)}
                              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white border border-surface-600 hover:border-surface-500 hover:bg-surface-700/50 px-3 py-1.5 rounded-lg transition-colors"
                            >
                              <Plus className="w-3.5 h-3.5" /> Nova planta
                            </button>
                            <button
                              onClick={() => openNewItem(entry.address.id)}
                              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white border border-surface-600 hover:border-surface-500 hover:bg-surface-700/50 px-3 py-1.5 rounded-lg transition-colors"
                            >
                              <Plus className="w-3.5 h-3.5" /> Nova medida sem planta
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>

      {modal === 'address' && (
        <Drawer title={editingAddr ? 'Editar endereço' : 'Novo endereço'} onClose={closeModal}>
          <div className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">Endereço completo *</label>
              <input
                className="input"
                placeholder="Rua das Flores, 123 — Bairro"
                value={addrForm.raw_address}
                onChange={(e) => setAddrForm({ ...addrForm, raw_address: e.target.value })}
              />
              <p className="text-slate-600 text-xs mt-1.5 flex items-center gap-1">
                <Info className="w-3 h-3" />
                O bot usa esse texto para encontrar o endereço pelo cliente.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Cidade</label>
                <input className="input" placeholder="São Paulo" value={addrForm.city} onChange={(e) => setAddrForm({ ...addrForm, city: e.target.value })} />
              </div>
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Estado</label>
                <select className="input" value={addrForm.state} onChange={(e) => setAddrForm({ ...addrForm, state: e.target.value })}>
                  <option value="">Selecione</option>
                  {BR_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">CEP</label>
              <input className="input" placeholder="01310-100" value={addrForm.zipcode} onChange={(e) => setAddrForm({ ...addrForm, zipcode: e.target.value })} />
            </div>
            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">Observações internas</label>
              <textarea className="input min-h-[80px] resize-none" placeholder="Referências, complemento..." value={addrForm.notes} onChange={(e) => setAddrForm({ ...addrForm, notes: e.target.value })} />
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={closeModal} className="btn-secondary flex-1">Cancelar</button>
              <button onClick={handleSaveAddress} disabled={saving || !addrForm.raw_address.trim()} className="btn-primary flex-1 flex items-center justify-center gap-2">
                {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : null}
                {saving ? 'Salvando...' : 'Salvar endereço'}
              </button>
            </div>
          </div>
        </Drawer>
      )}

      {modal === 'plant' && (
        <Modal title={editingPlant ? 'Editar planta' : 'Nova planta'} onClose={closeModal}>
          <div className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">Nome da planta *</label>
              <input
                className="input"
                placeholder="Apto 101, Sala principal, Cozinha..."
                value={plantForm.name}
                onChange={(e) => setPlantForm({ ...plantForm, name: e.target.value })}
                autoFocus
              />
              <p className="text-slate-600 text-xs mt-1.5 flex items-center gap-1">
                <Info className="w-3 h-3" />
                O nome da planta é sempre visível ao cliente no bot.
              </p>
            </div>
            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">Ordem de exibição</label>
              <input className="input" type="number" min={0} value={plantForm.sort_order} onChange={(e) => setPlantForm({ ...plantForm, sort_order: e.target.value })} />
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={closeModal} className="btn-secondary flex-1">Cancelar</button>
              <button onClick={handleSavePlant} disabled={saving || !plantForm.name.trim()} className="btn-primary flex-1 flex items-center justify-center gap-2">
                {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : null}
                {saving ? 'Salvando...' : 'Salvar planta'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {modal === 'item' && (
        <Modal title={editingItem ? 'Editar medida' : 'Nova medida'} onClose={closeModal}>
          <div className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">Descrição *</label>
              <input className="input" placeholder="Ex: Janela da sala" value={itemForm.label} onChange={(e) => setItemForm({ ...itemForm, label: e.target.value })} autoFocus />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Largura (m) *</label>
                <input className="input" type="number" step="0.01" min="0.01" placeholder="1.80" value={itemForm.width_m} onChange={(e) => setItemForm({ ...itemForm, width_m: e.target.value })} />
              </div>
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Altura (m) *</label>
                <input className="input" type="number" step="0.01" min="0.01" placeholder="1.50" value={itemForm.height_m} onChange={(e) => setItemForm({ ...itemForm, height_m: e.target.value })} />
              </div>
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Qtd.</label>
                <input className="input" type="number" min="1" value={itemForm.quantity} onChange={(e) => setItemForm({ ...itemForm, quantity: e.target.value })} />
              </div>
            </div>
            {areaCalc && (
              <div className="bg-brand-500/10 border border-brand-500/20 rounded-xl px-4 py-3 flex items-center justify-between">
                <span className="text-slate-400 text-sm">Área calculada</span>
                <span className="text-brand-300 font-bold text-lg tabular-nums">{areaCalc} m²</span>
              </div>
            )}
            {targetEntry && targetEntry.plants.length > 0 && (
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Planta (opcional)</label>
                <select className="input" value={itemForm.plant_id} onChange={(e) => setItemForm({ ...itemForm, plant_id: e.target.value })}>
                  <option value="">Sem planta</option>
                  {targetEntry.plants.map((pw) => (
                    <option key={pw.plant.id} value={String(pw.plant.id)}>{pw.plant.name}</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="block text-slate-400 text-sm font-medium mb-1.5">Observações</label>
              <input className="input" placeholder="Opcional" value={itemForm.notes} onChange={(e) => setItemForm({ ...itemForm, notes: e.target.value })} />
            </div>
            <div className="flex gap-3 pt-1">
              <button onClick={closeModal} className="btn-secondary flex-1">Cancelar</button>
              <button
                onClick={handleSaveItem}
                disabled={saving || !itemForm.label.trim() || !itemForm.width_m || !itemForm.height_m}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : null}
                {saving ? 'Salvando...' : 'Salvar medida'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

function ItemTable({ items, onEdit, onDelete }: {
  items: MeasureItem[]
  onEdit: (item: MeasureItem) => void
  onDelete: (id: number) => void
}) {
  const total = items.reduce((s, it) => s + Number(it.area_m2 ?? 0), 0)
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-700">
            <th className="text-left text-slate-500 font-medium px-4 py-2 text-xs">Descrição</th>
            <th className="text-right text-slate-500 font-medium px-3 py-2 text-xs">L (m)</th>
            <th className="text-right text-slate-500 font-medium px-3 py-2 text-xs">A (m)</th>
            <th className="text-right text-slate-500 font-medium px-3 py-2 text-xs">Qtd</th>
            <th className="text-right text-slate-500 font-medium px-3 py-2 text-xs">m²</th>
            <th className="px-3 py-2 w-16" />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b border-surface-700/50 last:border-0 hover:bg-surface-700/20 group transition-colors">
              <td className="px-4 py-2.5">
                <p className="text-white text-sm">{item.label}</p>
                {item.notes && <p className="text-slate-600 text-xs truncate max-w-[200px] mt-0.5">{item.notes}</p>}
              </td>
              <td className="px-3 py-2.5 text-right text-slate-300 font-mono text-xs tabular-nums">{Number(item.width_m).toFixed(2)}</td>
              <td className="px-3 py-2.5 text-right text-slate-300 font-mono text-xs tabular-nums">{Number(item.height_m).toFixed(2)}</td>
              <td className="px-3 py-2.5 text-right text-slate-400 text-xs">{item.quantity}</td>
              <td className="px-3 py-2.5 text-right text-brand-400 font-semibold font-mono text-xs tabular-nums">{Number(item.area_m2).toFixed(2)}</td>
              <td className="px-3 py-2.5">
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity justify-end">
                  <button onClick={() => onEdit(item)} className="p-1.5 text-slate-500 hover:text-white rounded-lg hover:bg-surface-600 transition-colors">
                    <Pencil className="w-3 h-3" />
                  </button>
                  <button onClick={() => onDelete(item.id)} className="p-1.5 text-slate-500 hover:text-red-400 rounded-lg hover:bg-red-500/10 transition-colors">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
        {items.length > 1 && (
          <tfoot>
            <tr className="border-t border-surface-600">
              <td colSpan={4} className="px-4 py-2 text-xs text-slate-500 font-medium">Total</td>
              <td className="px-3 py-2 text-right text-brand-300 font-bold font-mono text-xs tabular-nums">{total.toFixed(2)}</td>
              <td />
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  )
}
