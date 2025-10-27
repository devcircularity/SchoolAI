// services/systemSettings.ts - New service for system settings

import { apiClient } from './api';

export interface QueueVisibilitySetting {
  hidden: boolean;
  updated_at: string | null;
  updated_by: string | null;
}

class SystemSettingsService {
  async getQueueVisibility(): Promise<QueueVisibilitySetting> {
    const response = await apiClient.get('/api/admin/configuration/settings/hide-tester-queue');
    return response.data;
  }

  async setQueueVisibility(hidden: boolean): Promise<{
    message: string;
    hidden: boolean;
    updated_at: string;
    updated_by: string;
  }> {
    const response = await apiClient.post('/api/admin/configuration/settings/hide-tester-queue', {
      hidden
    });
    return response.data;
  }
}

export const systemSettingsService = new SystemSettingsService();