// app/login/page.tsx - Final working version
"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { authService } from "@/services/auth";
import { useState, Suspense } from "react";
import Link from "next/link";
import AuthLayout from "@/components/auth/AuthLayout";
import TextField from "@/components/ui/TextField";
import PasswordField from "@/components/ui/PasswordField";
import Button from "@/components/ui/Button";

function LoginForm() {
  const router = useRouter();
  const sp = useSearchParams();
  const next = sp.get("next") || "/";
  const { login, setSchoolId } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onLogin(e: React.FormEvent) {
    e.preventDefault();
    
    // Clear any existing errors
    setErr(null);
    
    // Basic validation
    if (!email.trim()) {
      setErr("Email is required");
      return;
    }
    
    if (!password.trim()) {
      setErr("Password is required");
      return;
    }
    
    setLoading(true);
    
    try {
      const res = await authService.login({ email: email.trim(), password });
      
      // Backend returns 'access_token' field, not 'token'
      const token = res?.access_token;
      if (!token) {
        console.error("Login response:", res);
        throw new Error("No access token in response");
      }
      
      await login({ token });
      
      // Backend returns 'school_id' field
      const schoolId = res?.school_id;
      if (schoolId) {
        setSchoolId(schoolId.toString());
        router.replace(next);
      } else {
        router.replace(`/onboarding/school?next=${encodeURIComponent(next)}`);
      }
    } catch (e: any) {
      console.error("Login error:", e);
      
      // Enhanced error handling with specific messages
      let errorMessage = "Login failed";
      
      if (e?.response?.status === 401) {
        errorMessage = "Invalid email or password";
      } else if (e?.response?.status === 400) {
        errorMessage = e?.response?.data?.detail || "Invalid request";
      } else if (e?.response?.status >= 500) {
        errorMessage = "Server error. Please try again later.";
      } else if (e?.message?.includes("Network Error") || e?.code === "ECONNREFUSED") {
        errorMessage = "Unable to connect to server. Please check your connection.";
      } else if (e?.response?.data?.detail) {
        errorMessage = e.response.data.detail;
      } else if (e?.message) {
        errorMessage = e.message;
      }
      
      setErr(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  // Clear error when user starts typing
  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    if (err) setErr(null);
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    if (err) setErr(null);
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to manage your school">
      <form onSubmit={onLogin} className="space-y-4" noValidate>
        <TextField
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={handleEmailChange}
          placeholder="email address"
          autoComplete="email"
          required
        />
        <PasswordField
          id="password"
          label="Password"
          value={password}
          onChange={handlePasswordChange}
          placeholder="Password"
          autoComplete="current-password"
          required
        />
        
        <Button 
          type="submit"
          className="w-full" 
          disabled={loading || !email.trim() || !password.trim()}
        >
          {loading ? "Signing in…" : "Continue"}
        </Button>
      </form>

      <div className="flex items-center justify-between text-sm mt-4">
        <Link href="/forgot-password" className="link">Forgot password?</Link>
        <span className="opacity-80">
          Don't have an account? <Link href="/signup" className="link">Create one</Link>
        </span>
      </div>

      {/* Error display */}
      {err && (
        <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800/30">
          <p className="text-red-700 dark:text-red-300 text-sm font-medium" role="alert" aria-live="assertive">
            {err}
          </p>
        </div>
      )}
    </AuthLayout>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}