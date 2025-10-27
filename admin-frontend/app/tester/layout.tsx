// app/tester/layout.tsx
"use client";
import React, { useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import WorkspaceShell from "@/components/layout/WorkspaceShell";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";

export default function TesterLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  
  // Set the header title for tester section
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Tester Dashboard',
      subtitle: 'Monitor and improve AI responses' 
    });
    
    // Clean up on unmount
    return () => HeaderTitleBus.send({ type: 'clear' });
  }, []);
  
  useEffect(() => {
    // Wait for auth to finish loading
    if (isLoading) return;

    // Redirect to login if not authenticated
    if (!isAuthenticated || !user) {
      router.replace("/login");
      return;
    }

    // Check if user has tester permissions directly instead of using canAccessTesterQueue to avoid type issues
    const hasTesterPermission = user.permissions?.is_tester || 
                               user.permissions?.is_admin || 
                               user.permissions?.is_super_admin ||
                               user.roles?.includes("TESTER") ||
                               user.roles?.includes("ADMIN") ||
                               user.roles?.includes("SUPER_ADMIN");

    if (!hasTesterPermission) {
      console.log("User lacks tester permissions, redirecting...", {
        userRoles: user.roles,
        userPermissions: user.permissions,
      });
      
      // Route based on user's actual role
      if (user.roles?.includes("ADMIN") || user.roles?.includes("SUPER_ADMIN")) {
        router.replace("/admin");
      } else {
        router.replace("/dashboard");
      }
      return;
    }
  }, [user, isLoading, isAuthenticated, router]);
  
  // Show loading state while auth is being determined
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white dark:bg-neutral-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-neutral-600 dark:text-neutral-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render anything while redirecting
  if (!isAuthenticated || !user) {
    return null;
  }
  
  // Check permissions again for render guard
  const hasTesterPermission = user.permissions?.is_tester || 
                             user.permissions?.is_admin || 
                             user.permissions?.is_super_admin ||
                             user.roles?.includes("TESTER") ||
                             user.roles?.includes("ADMIN") ||
                             user.roles?.includes("SUPER_ADMIN");
  
  // Don't render anything while redirecting non-tester users
  if (!hasTesterPermission) {
    return null;
  }
  
  // Use the unified WorkspaceShell instead of custom tester layout
  return (
    <WorkspaceShell>
      {children}
    </WorkspaceShell>
  );
}