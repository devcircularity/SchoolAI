// services/classes.ts
import { api } from './api'

type CreateClassRequest = {
  name: string
}

type Class = {
  id: number
  name: string
  school_id: number
}

export const classService = {
  async list() {
    const { data } = await api.get('/api/classes')
    return data as Class[]
  },
  
  async create(body: CreateClassRequest) {
    const { data } = await api.post('/api/classes', body)
    return data as Class
  }
}

// Export individual functions for convenience
export const listClasses = classService.list
export const createClass = classService.create