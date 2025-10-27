import { UserInfo } from '@/services/auth';

/**
 * Check if a user has valid roles/permissions to access the application
 */
export function checkUserHasValidRole(user: UserInfo | null): boolean {
  if (!user) return false;
  
  // Check for valid roles/permissions
  const hasValidRole = 
    user.roles?.includes("TESTER") || 
    user.permissions?.is_admin || 
    user.permissions?.is_super_admin;
  
  return !!hasValidRole;
}

/**
 * Get the appropriate redirect path based on user role
 */
export function getUserRedirectPath(user: UserInfo): string {
  if (user.roles?.includes("TESTER")) {
    return "/tester";
  } else if (user.permissions?.is_admin || user.permissions?.is_super_admin) {
    return "/admin";
  }
  
  // Default fallback - this should be handled in the calling code
  return "/";
}

/**
 * Check if user is a tester
 */
export function isUserTester(user: UserInfo | null): boolean {
  return user?.roles?.includes("TESTER") || false;
}

/**
 * Check if user is an admin
 */
export function isUserAdmin(user: UserInfo | null): boolean {
  return user?.permissions?.is_admin || false;
}

/**
 * Check if user is a super admin
 */
export function isUserSuperAdmin(user: UserInfo | null): boolean {
  return user?.permissions?.is_super_admin || false;
}

/**
 * Check if user has any admin privileges
 */
export function hasAdminPrivileges(user: UserInfo | null): boolean {
  return isUserAdmin(user) || isUserSuperAdmin(user);
}