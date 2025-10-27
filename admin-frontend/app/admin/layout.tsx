// app/admin/layout.tsx
"use client";
import React, { useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import WorkspaceShell from "@/components/layout/WorkspaceShell";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  
  // Remove the HeaderTitleBus code from here - let pages set their own titles
  
  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated || !user) {
      router.replace("/login");
      return;
    }

    const isAdmin = user.roles?.includes("ADMIN") || 
                   user.roles?.includes("SUPER_ADMIN") ||
                   user.permissions?.is_admin ||
                   user.permissions?.is_super_admin;

    if (!isAdmin) {
      console.log("User lacks admin permissions, redirecting...", {
        userRoles: user.roles,
        userPermissions: user.permissions,
      });
      
      if (user.roles?.includes("TESTER")) {
        router.replace("/tester");
      } else {
        router.replace("/dashboard");
      }
      return;
    }
  }, [user, isLoading, isAuthenticated, router]);
  
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

  if (!isAuthenticated || !user) {
    return null;
  }
  
  const isAdmin = user.roles?.includes("ADMIN") || 
                 user.roles?.includes("SUPER_ADMIN") ||
                 user.permissions?.is_admin ||
                 user.permissions?.is_super_admin;
  
  if (!isAdmin) {
    return null;
  }
  
  return (
    <WorkspaceShell>
      {children}
    </WorkspaceShell>
  );
}