// components/auth/RouteProtection.tsx
"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect, ReactNode } from "react";

interface RouteProtectionProps {
  children: ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  fallbackRoute?: string;
  allowedForAll?: boolean; // If true, just requires authentication
}

export function RouteProtection({ 
  children, 
  requiredRoles = [], 
  requiredPermissions = [],
  fallbackRoute = "/dashboard",
  allowedForAll = false
}: RouteProtectionProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Wait for auth to finish loading
    if (isLoading) return;

    // Redirect to login if not authenticated
    if (!isAuthenticated || !user) {
      router.replace("/login");
      return;
    }

    // If allowedForAll is true, just check authentication
    if (allowedForAll) return;

    // Check role requirements
    if (requiredRoles.length > 0) {
      const hasRequiredRole = requiredRoles.some(role => 
        user.roles?.includes(role)
      );
      
      if (!hasRequiredRole) {
        router.replace(fallbackRoute);
        return;
      }
    }

    // Check permission requirements
    if (requiredPermissions.length > 0) {
      const hasRequiredPermission = requiredPermissions.some(permission => {
        switch (permission) {
          case 'is_admin':
            return user.permissions?.is_admin;
          case 'is_super_admin':
            return user.permissions?.is_super_admin;
          case 'is_tester':
            return user.permissions?.is_tester;
          case 'can_manage_users':
            return user.permissions?.can_manage_users;
          case 'can_manage_intent_config':
            return user.permissions?.can_manage_intent_config;
          default:
            return false;
        }
      });
      
      if (!hasRequiredPermission) {
        router.replace(fallbackRoute);
        return;
      }
    }
  }, [user, isAuthenticated, isLoading, router, requiredRoles, requiredPermissions, fallbackRoute, allowedForAll]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-neutral-600 dark:text-neutral-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render children if not authenticated
  if (!isAuthenticated || !user) {
    return null;
  }

  // Don't render if role/permission check fails (will redirect via useEffect)
  if (!allowedForAll) {
    if (requiredRoles.length > 0) {
      const hasRequiredRole = requiredRoles.some(role => 
        user.roles?.includes(role)
      );
      if (!hasRequiredRole) return null;
    }

    if (requiredPermissions.length > 0) {
      const hasRequiredPermission = requiredPermissions.some(permission => {
        switch (permission) {
          case 'is_admin':
            return user.permissions?.is_admin;
          case 'is_super_admin':
            return user.permissions?.is_super_admin;
          case 'is_tester':
            return user.permissions?.is_tester;
          case 'can_manage_users':
            return user.permissions?.can_manage_users;
          default:
            return false;
        }
      });
      if (!hasRequiredPermission) return null;
    }
  }

  return <>{children}</>;
}

// Convenience wrapper components for common use cases
export function TesterRoute({ children }: { children: ReactNode }) {
  return (
    <RouteProtection requiredRoles={["TESTER"]}>
      {children}
    </RouteProtection>
  );
}

export function AdminRoute({ children }: { children: ReactNode }) {
  return (
    <RouteProtection requiredPermissions={["is_admin"]}>
      {children}
    </RouteProtection>
  );
}

export function SuperAdminRoute({ children }: { children: ReactNode }) {
  return (
    <RouteProtection requiredPermissions={["is_super_admin"]}>
      {children}
    </RouteProtection>
  );
}

export function AuthenticatedRoute({ children }: { children: ReactNode }) {
  return (
    <RouteProtection allowedForAll={true}>
      {children}
    </RouteProtection>
  );
}