"use client";

import React, { useState, useEffect } from "react";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import AnalysisResultComponent from "@/components/AnalysisResult";
import { apiGet, BASE_URL } from "@/lib/api";
import type { SceneAnalysis } from "@/types";
import styles from "./page.module.css";

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function ConfidencePill({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const cls =
    pct >= 80
      ? styles.confHigh
      : pct >= 50
        ? styles.confMed
        : styles.confLow;
  return (
    <span className={`${styles.confidencePill} ${cls}`}>
      {pct}%
    </span>
  );
}

function HistoryContent() {
  const [analyses, setAnalyses] = useState<SceneAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    apiGet<SceneAnalysis[]>("/api/v1/analyses")
      .then(setAnalyses)
      .catch((err) => setError(err.message ?? "Failed to load history"))
      .finally(() => setLoading(false));
  }, []);

  const toggleExpand = (id: number) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="page-content container container-md">
        <div className={`${styles.header} animate-fade-in-up`}>
          <h2>
            Analysis <span className="text-gradient">History</span>
          </h2>
          <p className="text-secondary mt-2">
            Browse your past scene analyses and revisit detailed breakdowns.
          </p>
        </div>

        {error && (
          <div className="card animate-fade-in" style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "var(--sp-6)",
            borderColor: "rgba(239, 68, 68, 0.2)",
            background: "rgba(239, 68, 68, 0.06)",
          }}>
            <p className="form-error">⚠️ {error}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => setError(null)}>
              Dismiss
            </button>
          </div>
        )}

        {loading ? (
          <div className={styles.grid}>
            {[1, 2, 3].map((i) => (
              <div key={i} className={styles.skeletonCard}>
                <div className={`skeleton ${styles.skeletonIcon}`} />
                <div className={styles.skeletonText}>
                  <div className={`skeleton ${styles.skeletonTitle}`} />
                  <div className={`skeleton ${styles.skeletonMeta}`} />
                </div>
                <div className={`skeleton ${styles.skeletonPill}`} />
              </div>
            ))}
          </div>
        ) : analyses.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <h3 className="empty-state-title">No History Yet</h3>
            <p className="empty-state-desc">
              You haven't analyzed any scenes yet. Go to the Analyze tab to get started.
            </p>
          </div>
        ) : (
          <div className={styles.grid}>
            {analyses.map((a, index) => {
              const isExpanded = expandedId === a.id;
              return (
                <div
                  key={a.id}
                  className={`${styles.card} animate-fade-in-up`}
                  style={{ animationDelay: `${index * 60}ms` }}
                  onClick={() => toggleExpand(a.id)}
                >
                  <div className={styles.cardHeader}>
                    <div className={styles.cardIcon}>📸</div>
                    <div className={styles.cardInfo}>
                      <div className={styles.cardModel}>
                        {a.scene ? `Scene ${a.scene.scene_number}: ${a.scene.title}` : "Unattached Analysis"}
                      </div>
                      <div className={styles.cardMeta}>
                        <span>{timeAgo(a.created_at)}</span>
                        <span>Model: {a.model_used}</span>
                      </div>
                    </div>
                    <ConfidencePill score={a.confidence_score} />
                  </div>
                  <div className={styles.expandBar}>
                    <span>{isExpanded ? "Collapse" : "View details"}</span>
                    <span className={`${styles.expandArrow} ${isExpanded ? styles.expandArrowOpen : ""}`}>▼</span>
                  </div>
                  {isExpanded && (
                    <div className={styles.expandedContent} onClick={(e) => e.stopPropagation()}>
                      <AnalysisResultComponent 
                        result={a.analysis_result} 
                        imageUrl={a.image_path ? `${BASE_URL}/${a.image_path}` : undefined} 
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function HistoryPage() {
  return (
    <AuthGuard>
      <HistoryContent />
    </AuthGuard>
  );
}
