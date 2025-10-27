// app/signup/page.tsx
"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { authService } from "@/services/auth";
import AuthLayout from "@/components/auth/AuthLayout";
import TextField from "@/components/ui/TextField";
import PasswordField from "@/components/ui/PasswordField";
import Button from "@/components/ui/Button";

function SignupForm() {
  const router = useRouter();
  const sp = useSearchParams();
  const next = sp.get("next") || "/";
  const { login, setSchoolId } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    if (password !== confirm) {
      setErr("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      const res = await authService.signup({
        full_name: fullName,
        email,
        password
      });
      
      // Backend returns 'access_token' field, not 'token'
      const token = res?.access_token;
      if (!token) {
        console.error("Signup response:", res);
        throw new Error("No access token returned");
      }

      await login({ token });
      
      // For signup, there might not be a school_id yet, but check anyway
      const schoolId = res?.school_id ?? null;
      if (schoolId) {
        setSchoolId(schoolId);
        router.replace(next);
      } else {
        router.replace(`/onboarding/school?next=${encodeURIComponent(next)}`);
      }
    } catch (e: any) {
      console.error("Signup error:", e);
      setErr(e?.response?.data?.detail || e?.message || "Sign up failed");
    } finally {
      setLoading(false);
    }
  }

  const passwordsMatch = !password || !confirm || password === confirm;

  return (
    <AuthLayout title="Create your account" subtitle="Start organizing your school">
      <form onSubmit={onCreate} className="space-y-4" noValidate>
        <TextField
          id="full-name"
          label="Full name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Jane Doe"
          autoComplete="name"
          required
        />
        <TextField
          id="signup-email"
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          required
        />
        <PasswordField
          id="signup-password"
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          helperText="Use at least 6 characters."
          autoComplete="new-password"
          required
        />
        <PasswordField
          id="confirm-password"
          label="Confirm password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Password"
          autoComplete="new-password"
          required
          error={password && confirm && password !== confirm ? "Passwords do not match" : null}
        />
        <Button className="w-full" disabled={loading || !passwordsMatch}>
          {loading ? "Creating…" : "Create account"}
        </Button>
      </form>

      <div className="flex items-center justify-between text-sm mt-4">
        <span className="opacity-80">
          Already have an account? <Link className="link" href="/login">Sign in</Link>
        </span>
        <Link href="/forgot-password" className="link">Forgot password?</Link>
      </div>

      {err && <p className="error-text mt-3" role="alert" aria-live="polite">{err}</p>}
    </AuthLayout>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SignupForm />
    </Suspense>
  );
}