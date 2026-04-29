"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { isAuthenticated } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    } else {
      setChecking(false);
    }
  }, [router]);

  if (checking) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#F2F2F7]">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-[#007AFF] border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
