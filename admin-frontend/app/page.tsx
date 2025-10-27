// app/page.tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function HomePage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Wait for auth to finish loading
    if (isLoading) return;

    if (!isAuthenticated || !user) {
      router.replace("/login");
      return;
    }

    // Check user roles and route accordingly
    if (user.roles?.includes("TESTER")) {
      router.replace("/tester");
    } else if (user.permissions?.is_admin || user.permissions?.is_super_admin) {
      router.replace("/admin");
    } else {
      // Default route for other authenticated users (like PARENT role)
      router.replace("/dashboard");
    }
  }, [user, isAuthenticated, isLoading, router]);

  // Show loading state while determining route
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-neutral-600 dark:text-neutral-400">Redirecting...</p>
      </div>
    </div>
  );
}