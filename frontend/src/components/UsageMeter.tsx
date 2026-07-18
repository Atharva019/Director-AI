"use client";

import React, { useEffect, useState } from "react";

import { apiGet } from "@/lib/api";
import styles from "./UsageMeter.module.css";

export interface Usage {
  plan: string;
  analyses: { used: number; limit: number };
  projects: { used: number; limit: number };
}

interface Props {
  /** Which counter to show. */
  resource: "analyses" | "projects";
  /** Bump this to refetch after the count changes. */
  refreshKey?: number;
}

export default function UsageMeter({ resource, refreshKey = 0 }: Props) {
  const [usage, setUsage] = useState<Usage | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<Usage>("/api/v1/auth/usage")
      .then((u) => {
        if (!cancelled) setUsage(u);
      })
      .catch(() => {
        // The meter is decorative — a failure here must never block the page.
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  if (!usage || usage.plan === "pro") return null;

  const { used, limit } = usage[resource];
  const pct = Math.min(100, Math.round((used / limit) * 100));
  const exhausted = used >= limit;

  return (
    <div className={styles.wrapper}>
      <div className={styles.row}>
        <span className={styles.label}>
          {used} of {limit} {resource} used
        </span>
        {exhausted && <span className={styles.badge}>Limit reached</span>}
      </div>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={used}
        aria-valuemin={0}
        aria-valuemax={limit}
        aria-label={`${resource} used`}
      >
        <div
          className={`${styles.fill} ${exhausted ? styles.fillFull : ""}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
