// utils/permissions.ts
import { UserInfo } from '@/services/auth';

export function isAdmin(user: UserInfo | null): boolean {
  if (!user) return false;
  
  return user.permissions?.is_admin || 
         user.permissions?.is_super_admin || 
         user.roles?.includes('ADMIN') || 
         user.roles?.includes('SUPER_ADMIN') || 
         false;
}

export function isSuperAdmin(user: UserInfo | null): boolean {
  if (!user) return false;
  
  return user.permissions?.is_super_admin || 
         user.roles?.includes('SUPER_ADMIN') || 
         false;
}

export function canManageUsers(user: UserInfo | null): boolean {
  if (!user) return false;
  
  return user.permissions?.can_manage_users || 
         isAdmin(user);
}

export function canManageIntentConfig(user: UserInfo | null): boolean {
  if (!user) return false;
  
  // If the specific permission exists, use it; otherwise fall back to admin check
  return user.permissions?.can_manage_intent_config !== undefined 
    ? user.permissions.can_manage_intent_config 
    : isAdmin(user);
}

export function canAccessTesterQueue(user: UserInfo | null): boolean {
  if (!user) return false;
  
  // Simplified check - use existing permissions or fall back to admin/tester roles
  return isAdmin(user) || 
         user.permissions?.is_tester === true || 
         user.roles?.includes('TESTER') || 
         false;
}

export function canViewLogs(user: UserInfo | null): boolean {
  if (!user) return false;
  
  // Simplified check - fall back to admin check
  return isAdmin(user);
}

export function canManageSchools(user: UserInfo | null): boolean {
  if (!user) return false;
  
  // Simplified check - fall back to super admin
  return isSuperAdmin(user);
}