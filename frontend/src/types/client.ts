import type { PaginatedResponse } from "@/types/dashboard"

export interface Client {
  id: string
  user_id: string
  email: string
  first_name: string
  last_name: string
  phone_number: string | null
  timezone: string
  created_at: string
  updated_at: string
}

export type PaginatedClients = PaginatedResponse<Client>

export interface ClientCreateInput {
  email: string
  password: string
  first_name: string
  last_name: string
  phone_number?: string | null
  timezone: string
}

export interface ClientUpdateInput {
  first_name?: string
  last_name?: string
  phone_number?: string | null
  timezone?: string
}
