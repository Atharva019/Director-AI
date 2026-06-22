"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import styles from "./page.module.css";

export default function LandingPage() {
  const { firebaseUser, loading, signInGoogle, signInEmail, signUpEmail } =
    useAuth();
  const router = useRouter();

  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && firebaseUser) {
      router.replace("/dashboard");
    }
  }, [loading, firebaseUser, router]);

  const handleGoogleSignIn = async () => {
    setError(null);
    try {
      await signInGoogle();
    } catch (err: any) {
      setError(err.message ?? "Google sign-in failed");
    }
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (isSignUp) {
        if (!name.trim()) {
          setError("Please enter your name");
          return;
        }
        await signUpEmail(email, password, name);
      } else {
        await signInEmail(email, password);
      }
    } catch (err: any) {
      setError(err.message ?? "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="full-center">
        <div className="spinner" />
      </div>
    );
  }

  if (firebaseUser) return null;

  return (
    <main className={styles.page}>
      {/* Background effects */}
      <div className={styles.bgGlow1} />
      <div className={styles.bgGlow2} />
      <div className={styles.bgGrid} />

      <div className={styles.container}>
        {/* Hero */}
        <div className={styles.hero}>
          <div className={styles.badge}>
            <span>🎬</span> AI-Powered Filmmaking
          </div>

          <h1 className={styles.title}>
            Director <span className="text-gradient">AI</span>
          </h1>

          <p className={styles.tagline}>
            Your AI cinematography partner. Analyze scenes, plan shots, and get
            professional lighting & camera recommendations.
          </p>

          <div className={styles.features}>
            <div className={styles.feature}>
              <span className={styles.featureIcon}>📸</span>
              <span>Scene Analysis</span>
            </div>
            <div className={styles.feature}>
              <span className={styles.featureIcon}>💡</span>
              <span>Lighting Setup</span>
            </div>
            <div className={styles.feature}>
              <span className={styles.featureIcon}>🎥</span>
              <span>Shot Planning</span>
            </div>
          </div>
        </div>

        {/* Auth card */}
        <div className={`card ${styles.authCard}`}>
          <h3 className={styles.authTitle}>
            {isSignUp ? "Create Account" : "Welcome Back"}
          </h3>
          <p className={`text-secondary text-sm ${styles.authSubtitle}`}>
            {isSignUp
              ? "Start your filmmaking journey"
              : "Sign in to continue"}
          </p>

          {/* Google button */}
          <button
            className={`${styles.googleBtn}`}
            onClick={handleGoogleSignIn}
          >
            <svg className={styles.googleIcon} viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </button>

          <div className={styles.divider}>
            <span>or</span>
          </div>

          {/* Toggle email form */}
          {!showEmailForm ? (
            <button
              className="btn btn-secondary"
              style={{ width: "100%" }}
              onClick={() => setShowEmailForm(true)}
            >
              ✉️ Continue with Email
            </button>
          ) : (
            <form
              onSubmit={handleEmailSubmit}
              className={styles.form}
            >
              {isSignUp && (
                <div className="form-group">
                  <label className="form-label">Name</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Your name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
              )}
              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  className="input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary btn-lg"
                disabled={submitting}
                style={{ width: "100%" }}
              >
                {submitting ? (
                  <div className="spinner spinner-sm" />
                ) : isSignUp ? (
                  "Create Account"
                ) : (
                  "Sign In"
                )}
              </button>
            </form>
          )}

          {error && <p className="form-error mt-3">{error}</p>}

          <p className={`text-sm text-center mt-4 ${styles.toggle}`}>
            {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
            <button
              className={styles.toggleBtn}
              onClick={() => {
                setIsSignUp((v) => !v);
                setError(null);
              }}
            >
              {isSignUp ? "Sign In" : "Sign Up"}
            </button>
          </p>
        </div>
      </div>
    </main>
  );
}
