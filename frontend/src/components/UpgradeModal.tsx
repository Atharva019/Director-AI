"use client";

import React, { useEffect, useState } from "react";

import { apiPost, QuotaError } from "@/lib/api";
import styles from "./UpgradeModal.module.css";

interface Props {
  /** The quota error that triggered this modal; null keeps it closed. */
  error: QuotaError | null;
  onClose: () => void;
}

type Status = "idle" | "sending" | "joined" | "failed";

const RESOURCE_LABEL: Record<string, string> = {
  analysis: "analyses this month",
  project: "projects",
};

/**
 * Shown when a free-tier user hits a limit. There is no billing yet — the CTA
 * collects an email so we can size demand before building checkout.
 */
export default function UpgradeModal({ error, onClose }: Props) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  // Reset per-open so a second limit hit doesn't show the previous result.
  useEffect(() => {
    if (error) {
      setStatus("idle");
      setEmail("");
    }
  }, [error]);

  useEffect(() => {
    if (!error) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [error, onClose]);

  if (!error) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("sending");
    try {
      await apiPost("/api/v1/waitlist", { email: email.trim(), source: "quota_modal" });
      setStatus("joined");
    } catch {
      setStatus("failed");
    }
  };

  const label = RESOURCE_LABEL[error.resource] ?? error.resource;

  return (
    <div
      className={styles.backdrop}
      onClick={onClose}
      role="presentation"
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="upgrade-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className={styles.close}
          onClick={onClose}
          aria-label="Close"
        >
          ×
        </button>

        <h2 id="upgrade-title" className={styles.title}>
          You&apos;ve used all {error.limit} {label}
        </h2>

        {status === "joined" ? (
          <p className={styles.success}>
            You&apos;re on the list. We&apos;ll email you when Pro opens up.
          </p>
        ) : (
          <>
            <p className={styles.body}>
              Pro removes the limits entirely. It isn&apos;t live yet — leave your
              email and you&apos;ll be first in line.
            </p>

            <form className={styles.form} onSubmit={handleSubmit}>
              <label className={styles.srOnly} htmlFor="upgrade-email">
                Email address
              </label>
              <input
                id="upgrade-email"
                className={styles.input}
                type="email"
                required
                placeholder="you@studio.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={status === "sending"}
              />
              <button
                type="submit"
                className={styles.submit}
                disabled={status === "sending"}
              >
                {status === "sending" ? "Joining…" : "Join the Pro waitlist"}
              </button>
            </form>

            {status === "failed" && (
              <p className={styles.error} role="alert">
                Couldn&apos;t save that — please try again.
              </p>
            )}
          </>
        )}

        <p className={styles.footnote}>
          Your free quota resets on the 1st of next month.
        </p>
      </div>
    </div>
  );
}
