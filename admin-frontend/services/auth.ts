// services/auth.ts
import { apiClient } from './api';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  school_id?: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
}

export interface RegisterResponse {
  access_token: string;
}

export interface SwitchSchoolRequest {
  school_id: string;
}

// Updated UserInfo interface to match what the AuthContext expects
export interface UserInfo {
  user_id: string;
  email: string;
  full_name?: string; // Made optional to match the original interface
  is_active: boolean;
  is_verified: boolean;
  roles?: string[]; // Made optional to match the original interface
  active_school_id?: string;
  last_login?: string;
  permissions?: {
    can_manage_users?: boolean;
    is_admin?: boolean;
    is_super_admin?: boolean;
    is_tester?: boolean;
    can_manage_intent_config?: boolean;
  };
}

export interface UserPermissions {
  can_chat: boolean;
  can_view_conversations: boolean;
  can_manage_students: boolean;
  can_manage_classes: boolean;
  can_manage_fees: boolean;
  can_manage_payments: boolean;
  can_manage_school: boolean;
  can_manage_users: boolean;
  can_view_logs: boolean;
  can_manage_intent_config: boolean;
  can_access_tester_queue: boolean;
  can_submit_suggestions: boolean;
  can_manage_all_schools: boolean;
  can_promote_admins: boolean;
  can_access_system_settings: boolean;
  roles: string[];
  primary_role: string;
}

class AuthService {
  /**
   * Login user with email and password
   */
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post('/api/auth/login', data);
    return response.data;
  }

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post('/api/auth/register', data);
    return response.data;
  }

  /**
   * Switch active school
   */
  async switchSchool(data: SwitchSchoolRequest): Promise<LoginResponse> {
    const response = await apiClient.post('/api/auth/switch-school', data);
    return response.data;
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<UserInfo> {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
  }

  /**
   * Get detailed user permissions
   */
  async getUserPermissions(): Promise<UserPermissions> {
    const response = await apiClient.get('/api/auth/permissions');
    return response.data;
  }

  /**
   * Check if user has specific role
   */
  hasRole(permissions: UserPermissions | null, role: string): boolean {
    return permissions?.roles?.includes(role) ?? false;
  }

  /**
   * Check if user has any of the specified roles
   */
  hasAnyRole(permissions: UserPermissions | null, roles: string[]): boolean {
    if (!permissions?.roles) return false;
    return roles.some(role => permissions.roles.includes(role));
  }

  /**
   * Check if user is admin (ADMIN or SUPER_ADMIN)
   */
  isAdmin(permissions: UserPermissions | null): boolean {
    return this.hasAnyRole(permissions, ['ADMIN', 'SUPER_ADMIN']);
  }

  /**
   * Check if user is super admin
   */
  isSuperAdmin(permissions: UserPermissions | null): boolean {
    return this.hasRole(permissions, 'SUPER_ADMIN');
  }

  /**
   * Check if user is tester
   */
  isTester(permissions: UserPermissions | null): boolean {
    return this.hasRole(permissions, 'TESTER');
  }

  /**
   * Get user's primary role for display purposes
   */
  getPrimaryRole(permissions: UserPermissions | null): string {
    return permissions?.primary_role ?? 'PARENT';
  }

  /**
   * Format role name for display
   */
  formatRoleName(role: string): string {
    const roleNames: Record<string, string> = {
      'SUPER_ADMIN': 'Super Admin',
      'ADMIN': 'Administrator',
      'TESTER': 'Tester',
      'TEACHER': 'Teacher',
      'ACCOUNTANT': 'Accountant',
      'PARENT': 'Parent'
    };
    return roleNames[role] || role;
  }

  /**
   * Get available actions based on permissions
   */
  getAvailableActions(permissions: UserPermissions | null): string[] {
    const actions: string[] = [];
    
    if (!permissions) return actions;

    if (permissions.can_manage_students) actions.push('manage_students');
    if (permissions.can_manage_classes) actions.push('manage_classes');
    if (permissions.can_manage_fees) actions.push('manage_fees');
    if (permissions.can_manage_payments) actions.push('manage_payments');
    if (permissions.can_manage_school) actions.push('manage_school');
    if (permissions.can_manage_users) actions.push('manage_users');
    if (permissions.can_view_logs) actions.push('view_logs');
    if (permissions.can_manage_intent_config) actions.push('manage_intent_config');
    if (permissions.can_access_tester_queue) actions.push('access_tester_queue');
    if (permissions.can_submit_suggestions) actions.push('submit_suggestions');
    if (permissions.can_manage_all_schools) actions.push('manage_all_schools');
    if (permissions.can_access_system_settings) actions.push('access_system_settings');

    return actions;
  }

  /**
   * Logout user (client-side only, no API call needed)
   */
  logout(): void {
    // Clear tokens from localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('active_school_id');
    }
  }

  /**
   * Get stored token
   */
  getStoredToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  }

  /**
   * Get stored school ID
   */
  getStoredSchoolId(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('active_school_id');
  }

  /**
   * Store token
   */
  storeToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  /**
   * Store school ID
   */
  storeSchoolId(schoolId: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('active_school_id', schoolId);
    }
  }
}

export const authService = new AuthService();