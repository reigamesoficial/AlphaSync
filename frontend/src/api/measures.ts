import api from './client'
import type {
  AddressWithHierarchy,
  MeasureStats,
  Plant,
  MeasureItem,
  PNSettings,
} from '../types'

export async function getMeasureStats(): Promise<MeasureStats> {
  const { data } = await api.get('/measures/stats')
  return data
}

export async function listAddresses(params?: {
  search?: string
  city?: string
  state?: string
}): Promise<AddressWithHierarchy[]> {
  const { data } = await api.get('/measures/addresses', { params })
  return data
}

export async function createAddress(payload: {
  raw_address: string
  city?: string
  state?: string
  zipcode?: string
  notes?: string
}): Promise<AddressWithHierarchy> {
  const { data } = await api.post('/measures/addresses', payload)
  return data
}

export async function updateAddress(
  id: number,
  payload: {
    raw_address?: string
    city?: string
    state?: string
    zipcode?: string
    notes?: string
  }
): Promise<AddressWithHierarchy> {
  const { data } = await api.patch(`/measures/addresses/${id}`, payload)
  return data
}

export async function deleteAddress(id: number): Promise<void> {
  await api.delete(`/measures/addresses/${id}`)
}

export async function createPlant(payload: {
  address_catalog_id: number
  name: string
  sort_order?: number
}): Promise<Plant> {
  const { data } = await api.post('/measures/plants', payload)
  return data
}

export async function updatePlant(
  id: number,
  payload: { name?: string; sort_order?: number; is_active?: boolean }
): Promise<Plant> {
  const { data } = await api.patch(`/measures/plants/${id}`, payload)
  return data
}

export async function deletePlant(id: number): Promise<void> {
  await api.delete(`/measures/plants/${id}`)
}

export async function createItem(payload: {
  address_catalog_id: number
  plant_id?: number | null
  label: string
  width_m: number
  height_m: number
  quantity?: number
  notes?: string
}): Promise<MeasureItem> {
  const { data } = await api.post('/measures/items', payload)
  return data
}

export async function updateItem(
  id: number,
  payload: {
    plant_id?: number | null
    label?: string
    width_m?: number
    height_m?: number
    quantity?: number
    notes?: string
  }
): Promise<MeasureItem> {
  const { data } = await api.patch(`/measures/items/${id}`, payload)
  return data
}

export async function deleteItem(id: number): Promise<void> {
  await api.delete(`/measures/items/${id}`)
}

export async function getPNSettings(): Promise<PNSettings> {
  const { data } = await api.get('/company/settings/protection-network')
  return data
}

export async function updatePNSettings(payload: Partial<PNSettings>): Promise<PNSettings> {
  const { data } = await api.patch('/company/settings/protection-network', payload)
  return data
}
