"use client";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isLoading, isAuthenticated, active_school_id } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const hasSchool = !!active_school_id;

  useEffect(() => {
    if (isLoading) return; // wait for hydration
    if (!isAuthenticated) {
      // Redirect to public instead of login
      router.replace('/');
      return;
    }
    if (isAuthenticated && !hasSchool && !pathname.startsWith("/onboarding")) {
      router.replace(`/onboarding/school?next=${encodeURIComponent(pathname)}`);
    }
  }, [isLoading, isAuthenticated, hasSchool, router, pathname]);

  if (isLoading) return null;
  if (!isAuthenticated) return null;
  if (isAuthenticated && !hasSchool && !pathname.startsWith("/onboarding")) return null;

  return <>{children}</>;
}