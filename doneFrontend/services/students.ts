// services/students.ts
import { api } from './api'

type CreateStudentRequest = {
  first_name: string
  last_name: string
  admission_no: string
}

type EnrollStudentRequest = {
  full_name: string
  admission_no: string
  class_name: string
}

type Student = {
  id: number
  first_name: string
  last_name: string
  admission_no: string
  school_id: number
}

export const studentService = {
  async list() {
    const { data } = await api.get('/api/students')
    return data as Student[]
  },
  
  async create(body: CreateStudentRequest) {
    const { data } = await api.post('/api/students', body)
    return data as Student
  },
  
  async enroll(body: EnrollStudentRequest) {
    const { data } = await api.post('/api/students/enroll', body)
    return data
  }
}

// Export individual functions for convenience
export const listStudents = studentService.list
export const createStudent = studentService.create
export const enrollStudent = studentService.enroll