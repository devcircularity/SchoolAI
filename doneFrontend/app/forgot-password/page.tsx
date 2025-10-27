// app/forgot-password/page.tsx
"use client";
import Link from "next/link";
import { useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { authService } from "@/services/auth";
import AuthLayout from "@/components/auth/AuthLayout";
import TextField from "@/components/ui/TextField";
import Button from "@/components/ui/Button";
import { CheckCircle } from "lucide-react";

function ForgotPasswordForm() {
  const router = useRouter();
  
  const [email, setEmail] = useState("");
  const [step, setStep] = useState<"request" | "sent">("request");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);

    try {
      await authService.requestPasswordReset(email);
      setStep("sent");
    } catch (e: any) {
      console.error("Password reset request error:", e);
      setErr(e?.response?.data?.detail || e?.message || "Failed to send reset email");
    } finally {
      setLoading(false);
    }
  }

  if (step === "sent") {
    return (
      <AuthLayout 
        title="Check your email" 
        subtitle="We've sent password reset instructions"
      >
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          
          <div className="space-y-2">
            <p className="text-neutral-600 dark:text-neutral-400">
              If an account with <strong>{email}</strong> exists, you'll receive password reset instructions shortly.
            </p>
            <p className="text-sm text-neutral-500 dark:text-neutral-500">
              Check your spam folder if you don't see the email within a few minutes.
            </p>
          </div>

          <div className="pt-4 space-y-3">
            <Button 
              onClick={() => setStep("request")} 
              className="w-full"
              variant="secondary"
            >
              Send another email
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

  return (
    <AuthLayout 
      title="Reset your password" 
      subtitle="Enter your email to receive reset instructions"
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <TextField
          id="reset-email"
          label="Email address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          required
          helperText="We'll send reset instructions to this email"
        />
        
        <Button 
          type="submit"
          className="w-full" 
          disabled={loading || !email.trim()}
        >
          {loading ? "Sending..." : "Send reset instructions"}
        </Button>
      </form>

      <div className="flex items-center justify-between text-sm mt-4">
        <Link href="/login" className="link">
          Back to sign in
        </Link>
        <span className="opacity-80">
          Don't have an account? <Link href="/signup" className="link">Create one</Link>
        </span>
      </div>

      {err && (
        <p className="error-text mt-3" role="alert" aria-live="polite">
          {err}
        </p>
      )}
    </AuthLayout>
  );
}

export default function ForgotPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ForgotPasswordForm />
    </Suspense>
  );
}