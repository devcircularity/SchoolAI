// services/user.ts
import { apiClient } from './api';

export interface User {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  school_count: number;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

export interface CreateUserRequest {
  email: string;
  full_name: string;
  password: string;
  roles?: string[];
  is_active?: boolean;
}

export interface UpdateUserRequest {
  full_name?: string;
  roles?: string[];
  is_active?: boolean;
  is_verified?: boolean;
}

export interface UpdateUserRolesRequest {
  roles: string[];
}

export interface UserStats {
  total_users: number;
  active_users: number;
  users_by_role: Record<string, number>;
  new_users_this_week: number;
  new_users_this_month: number;
}

export interface UserFilters {
  page?: number;
  limit?: number;
  search?: string;
  role?: string;
  active_only?: boolean;
}

class UserService {
  /**
   * Get all users with optional filters
   */
  async getUsers(filters?: UserFilters): Promise<UserListResponse> {
    const params = new URLSearchParams();
    
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.search) params.append('search', filters.search);
    if (filters?.role) params.append('role', filters.role);
    if (filters?.active_only) params.append('active_only', 'true');

    const response = await apiClient.get(`/api/admin/users?${params.toString()}`);
    return response.data;
  }

  /**
   * Get user statistics
   */
  async getUserStats(): Promise<UserStats> {
    const response = await apiClient.get('/api/admin/users/stats');
    return response.data;
  }

  /**
   * Get user by ID
   */
  async getUserById(userId: string): Promise<User> {
    const response = await apiClient.get(`/api/admin/users/${userId}`);
    return response.data;
  }

  /**
   * Create new user
   */
  async createUser(data: CreateUserRequest): Promise<User> {
    const response = await apiClient.post('/api/admin/users', data);
    return response.data;
  }

  /**
   * Update user
   */
  async updateUser(userId: string, data: UpdateUserRequest): Promise<User> {
    const response = await apiClient.put(`/api/admin/users/${userId}`, data);
    return response.data;
  }

  /**
   * Update user roles specifically
   */
  async updateUserRoles(userId: string, data: UpdateUserRolesRequest): Promise<User> {
    const response = await apiClient.put(`/api/admin/users/${userId}/roles`, data);
    return response.data;
  }

  /**
   * Deactivate user (soft delete)
   */
  async deactivateUser(userId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/admin/users/${userId}`);
    return response.data;
  }

  /**
   * Toggle user active status
   */
  async toggleUserStatus(userId: string): Promise<User> {
    // Since the backend doesn't have a specific toggle endpoint, we'll get the user first
    // then update with the opposite status
    const user = await this.getUserById(userId);
    return this.updateUser(userId, { is_active: !user.is_active });
  }

  /**
   * Get available user roles
   */
  async getAvailableRoles(): Promise<{
    roles: Array<{
      value: string;
      label: string;
      description: string;
    }>;
  }> {
    const response = await apiClient.get('/api/admin/users/roles/available');
    return response.data;
  }
}

export const userService = new UserService();