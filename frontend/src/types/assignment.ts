export interface Assignment {
  id: string
  client_id: string
  trainer_id: string
  is_primary: boolean
  assigned_at: string
  created_at: string
  updated_at: string
}

export interface AssignmentCreateInput {
  client_id: string
  trainer_id: string
  is_primary?: boolean
}

export interface AssignedClient {
  assignment_id: string
  client_id: string
  first_name: string
  last_name: string
  email: string
  phone_number: string | null
  timezone: string
  is_primary: boolean
}
