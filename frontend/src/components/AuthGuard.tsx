"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { firebaseUser, loading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!loading && !firebaseUser) {
      router.replace("/");
    }
  }, [loading, firebaseUser, router]);

  if (loading) {
    return (
      <div className="full-center">
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--sp-4)" }}>
          <div className="spinner" />
          <p className="text-secondary text-sm">Loading&hellip;</p>
        </div>
      </div>
    );
  }

  if (!firebaseUser) {
    return null;
  }

  return <>{children}</>;
}
