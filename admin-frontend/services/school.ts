// services/school.ts - Add this method or create new file
import { apiClient } from './api';

export interface SchoolStats {
  total_schools: number;
  active_schools: number;
  inactive_schools: number;
}

class SchoolService {
  async getSchoolStats(): Promise<SchoolStats> {
    const response = await apiClient.get('/api/admin/schools/stats');
    return response.data;
  }
}

export const schoolService = new SchoolService();