// app/login/page.tsx
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
    setErr(null);
    setLoading(true);
    try {
      const res = await authService.login({ email, password });
      
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
      setErr(e?.response?.data?.detail || e?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to manage your school">
      <form onSubmit={onLogin} className="space-y-4" noValidate>
        <TextField
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="email address"
          autoComplete="email"
          required
        />
        <PasswordField
          id="password"
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoComplete="current-password"
          required
        />
        <Button className="w-full" disabled={loading}>
          {loading ? "Signing in…" : "Continue"}
        </Button>
      </form>

      <div className="flex items-center justify-between text-sm mt-4">
        <a href="https://olaji.co" className="link" target="_blank" rel="noopener noreferrer">
          Forgot password?
        </a>
        <span className="opacity-80">
          Don't have an account? <Link href="/signup" className="link">Create one</Link>
        </span>
      </div>

      {err && (
        <p className="error-text mt-3" role="alert" aria-live="polite">{err}</p>
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