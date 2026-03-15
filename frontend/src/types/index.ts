export interface User {
  id: number
  company_id: number
  name: string
  email: string
  role: string
  is_active: boolean
}

export interface LoginResponse {
  token: string
  refresh_token: string
  expires_at: string
  user: User
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

export interface Client {
  id: number
  company_id: number
  name: string
  phone: string
  email: string | null
  address: string | null
  whatsapp_id: string | null
  lead_source: string
  status: 'lead' | 'qualified' | 'customer' | 'inactive'
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ConversationMessage {
  id: number
  company_id: number
  conversation_id: number
  direction: 'in' | 'out'
  type: string
  sender_name: string | null
  content: string | null
  media_url: string | null
  whatsapp_msg_id: string | null
  metadata_json: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Conversation {
  id: number
  company_id: number
  client_id: number | null
  assigned_to_id: number | null
  channel: string
  status: 'open' | 'assumed' | 'bot' | 'closed' | 'archived'
  external_id: string | null
  phone: string
  subject: string | null
  bot_step: string | null
  first_message_at: string | null
  last_message_at: string | null
  created_at: string
  updated_at: string
}

export interface QuoteItem {
  id: number
  quote_id: number
  company_id: number
  description: string
  service_type: string | null
  width_cm: string | null
  height_cm: string | null
  quantity: number
  unit_price: string
  total_price: string
  status: string
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Quote {
  id: number
  company_id: number
  client_id: number
  conversation_id: number | null
  seller_id: number | null
  code: string | null
  service_type: string
  title: string | null
  description: string | null
  subtotal: string
  discount: string
  total_value: string
  status: 'draft' | 'confirmed' | 'cancelled' | 'done' | 'expired'
  valid_until: string | null
  notes: string | null
  pdf_url: string | null
  items: QuoteItem[]
  created_at: string
  updated_at: string
}

export interface CompanySettings {
  id: number
  company_id: number
  brand_name: string | null
  primary_color: string | null
  secondary_color: string | null
  logo_url: string | null
  bot_name: string | null
  quote_prefix: string | null
  whatsapp_access_token: string | null
  whatsapp_verify_token: string | null
  calendar_provider: string | null
  calendar_id: string | null
  currency: string
  timezone: string
  extra_settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface DashboardSummary {
  conversations: {
    total: number
    open: number
    by_status: Record<string, number>
  }
  clients: {
    total: number
    by_status: Record<string, number>
  }
  quotes: {
    total: number
    by_status: Record<string, number>
  }
}

export interface MeasureItem {
  id: number
  address_catalog_id: number
  company_id: number
  plant_id: number | null
  label: string
  width_m: number
  height_m: number
  quantity: number
  notes: string | null
  is_active: boolean
  area_m2: number
}

export interface Plant {
  id: number
  address_catalog_id: number
  company_id: number
  name: string
  sort_order: number
  is_active: boolean
}

export interface PlantWithItems {
  plant: Plant
  items: MeasureItem[]
}

export interface Address {
  id: number
  company_id: number
  raw_address: string
  normalized_address: string
  city: string | null
  state: string | null
  zipcode: string | null
  notes: string | null
  is_active: boolean
}

export interface AddressWithHierarchy {
  address: Address
  plants: PlantWithItems[]
  direct_items: MeasureItem[]
}

export interface MeasureStats {
  total_addresses: number
  total_plants: number
  total_items: number
}

export interface PNSettings {
  show_measures_to_customer: boolean
  default_price_per_m2: number
  minimum_order_value: number
  visit_fee: number
  available_colors: string[]
  available_mesh_types: string[]
  mesh_prices: Record<string, number>
}
