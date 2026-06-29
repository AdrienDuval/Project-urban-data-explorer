"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { login, register } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await register(email, username, password);
    } catch (err) {
      // If the error is "Username already taken" it means the account was
      // actually created on a previous attempt — try logging in instead.
      const msg = err instanceof Error ? err.message : "Registration failed.";
      if (msg.toLowerCase().includes("already")) {
        try {
          await login(email, password);
          router.push("/dashboard");
          return;
        } catch {
          setError("Account may already exist. Try signing in instead.");
          setLoading(false);
          return;
        }
      }
      setError(msg);
      setLoading(false);
      return;
    }
    router.push("/dashboard");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F2F2F7] px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-[#007AFF] transition hover:opacity-70"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
            </svg>
            Back to home
          </Link>
          <h1 className="mt-6 text-[28px] font-bold tracking-tight text-[#1d1d1f]">Create account</h1>
          <p className="mt-1.5 text-[15px] text-[rgba(60,60,67,0.6)]">Join and start exploring Paris</p>
        </div>

        <div
          className="rounded-2xl bg-white p-8"
          style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.08), 0 0 1px rgba(0,0,0,0.06)" }}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[rgba(60,60,67,0.6)] uppercase tracking-wider">
                Username
              </label>
              <input
                type="text"
                required
                minLength={3}
                maxLength={32}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-[10px] border border-[rgba(60,60,67,0.29)] bg-[#F2F2F7] px-4 py-3 text-[15px] text-[#1d1d1f] placeholder-[rgba(60,60,67,0.3)] outline-none transition focus:border-[#007AFF] focus:ring-2 focus:ring-[#007AFF]/20"
                placeholder="paris_explorer"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[rgba(60,60,67,0.6)] uppercase tracking-wider">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-[10px] border border-[rgba(60,60,67,0.29)] bg-[#F2F2F7] px-4 py-3 text-[15px] text-[#1d1d1f] placeholder-[rgba(60,60,67,0.3)] outline-none transition focus:border-[#007AFF] focus:ring-2 focus:ring-[#007AFF]/20"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[rgba(60,60,67,0.6)] uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-[10px] border border-[rgba(60,60,67,0.29)] bg-[#F2F2F7] px-4 py-3 text-[15px] text-[#1d1d1f] placeholder-[rgba(60,60,67,0.3)] outline-none transition focus:border-[#007AFF] focus:ring-2 focus:ring-[#007AFF]/20"
                placeholder="Min. 8 characters"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[rgba(60,60,67,0.6)] uppercase tracking-wider">
                Confirm password
              </label>
              <input
                type="password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full rounded-[10px] border border-[rgba(60,60,67,0.29)] bg-[#F2F2F7] px-4 py-3 text-[15px] text-[#1d1d1f] placeholder-[rgba(60,60,67,0.3)] outline-none transition focus:border-[#007AFF] focus:ring-2 focus:ring-[#007AFF]/20"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="rounded-[10px] bg-red-50 px-4 py-2.5 text-sm text-red-600 border border-red-200">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full rounded-full bg-[#007AFF] px-4 py-3 text-[15px] font-medium text-white transition hover:bg-[#0071E3] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[rgba(60,60,67,0.6)]">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-[#007AFF] transition hover:opacity-70">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
