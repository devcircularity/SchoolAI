// app/reset-password/page.tsx
"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, Suspense, useEffect } from "react";
import { authService } from "@/services/auth";
import AuthLayout from "@/components/auth/AuthLayout";
import PasswordField from "@/components/ui/PasswordField";
import Button from "@/components/ui/Button";
import { CheckCircle, AlertCircle } from "lucide-react";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const email = searchParams.get("email");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [step, setStep] = useState<"loading" | "form" | "success" | "invalid">("loading");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Validate token on component mount
  useEffect(() => {
    if (!token || !email) {
      setStep("invalid");
      return;
    }

    // Optionally verify the token with the backend
    authService.verifyResetToken(token, email)
      .then(() => setStep("form"))
      .catch(() => setStep("invalid"));
  }, [token, email]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);

    if (password !== confirmPassword) {
      setErr("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setErr("Password must be at least 6 characters long");
      return;
    }

    if (!token || !email) {
      setErr("Invalid reset link");
      return;
    }

    setLoading(true);

    try {
      await authService.resetPassword(token, email, password);
      setStep("success");
    } catch (e: any) {
      console.error("Password reset error:", e);
      const errorMessage = e?.response?.data?.detail || e?.message;
      
      if (errorMessage?.includes("expired") || errorMessage?.includes("invalid")) {
        setStep("invalid");
      } else {
        setErr(errorMessage || "Failed to reset password");
      }
    } finally {
      setLoading(false);
    }
  }

  if (step === "loading") {
    return (
      <AuthLayout title="Verifying reset link" subtitle="Please wait...">
        <div className="text-center py-8">
          <div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-4 text-neutral-600 dark:text-neutral-400">
            Verifying your reset link...
          </p>
        </div>
      </AuthLayout>
    );
  }

  if (step === "success") {
    return (
      <AuthLayout 
        title="Password updated" 
        subtitle="Your password has been successfully changed"
      >
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          
          <div className="space-y-2">
            <p className="text-neutral-600 dark:text-neutral-400">
              You can now sign in with your new password.
            </p>
          </div>

          <div className="pt-4">
            <Button 
              onClick={() => router.push("/login")} 
              className="w-full"
            >
              Continue to sign in
            </Button>
          </div>
        </div>
      </AuthLayout>
    );
  }

  if (step === "invalid") {
    return (
      <AuthLayout 
        title="Invalid reset link" 
        subtitle="This link has expired or is invalid"
      >
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
          </div>
          
          <div className="space-y-2">
            <p className="text-neutral-600 dark:text-neutral-400">
              This password reset link has expired or is no longer valid.
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500">
              Reset links expire after 1 hour for security reasons.
            </p>
          </div>

          <div className="pt-4 space-y-3">
            <Button 
              onClick={() => router.push("/forgot-password")} 
              className="w-full"
            >
              Request new reset link
            </Button>
            
            <div className="text-sm">
              <Link href="/login" className="link">
                Back to sign in
              </Link>
            </div>
          </div>
        </div>
      </AuthLayout>
    );
  }

  const passwordsMatch = !password || !confirmPassword || password === confirmPassword;

  return (
    <AuthLayout 
      title="Set new password" 
      subtitle={`Reset password for ${email}`}
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <PasswordField
          id="new-password"
          label="New password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter new password"
          helperText="Use at least 6 characters"
          autoComplete="new-password"
          required
        />
        
        <PasswordField
          id="confirm-new-password"
          label="Confirm new password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm new password"
          autoComplete="new-password"
          required
          error={password && confirmPassword && password !== confirmPassword ? "Passwords do not match" : null}
        />
        
        <Button 
          type="submit"
          className="w-full" 
          disabled={loading || !passwordsMatch || !password.trim()}
        >
          {loading ? "Updating password..." : "Update password"}
        </Button>
      </form>

      <div className="text-center text-sm mt-4">
        <Link href="/login" className="link">
          Back to sign in
        </Link>
      </div>

      {err && (
        <p className="error-text mt-3" role="alert" aria-live="polite">
          {err}
        </p>
      )}
    </AuthLayout>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}