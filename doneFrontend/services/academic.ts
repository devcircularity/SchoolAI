// services/academic.ts
import { api } from './api'

type SetAcademicYearRequest = {
  academic_year_start: string  // YYYY-MM-DD format
}

type AcademicYearResponse = {
  academic_year_start: string
  message: string
}

export const academicService = {
  async setAcademicYear(body: SetAcademicYearRequest) {
    const { data } = await api.post('/api/schools/active/academic-year', body)
    return data as AcademicYearResponse
  }
}

// Export individual functions for convenience
export const setAcademicYear = academicService.setAcademicYear