"use client";

import React, { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { SceneAnalysis } from "@/types";
import AnalysisResultComponent from "./AnalysisResult";
import styles from "./ShotList.module.css"; // Reuse similar styles for container
import cardStyles from "./SceneCard.module.css";

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

interface Props {
  sceneId: number;
}

export default function SceneAnalyses({ sceneId }: Props) {
  const [analyses, setAnalyses] = useState<SceneAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    apiGet<SceneAnalysis[]>(`/api/v1/analyses?scene_id=${sceneId}`)
      .then(setAnalyses)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sceneId]);

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className="spinner spinner-sm" />
        <span className="text-tertiary text-sm">Loading analyses...</span>
      </div>
    );
  }

  if (analyses.length === 0) {
    return null; // Don't show anything if no analyses
  }

  return (
    <div className={cardStyles.analysesContainer} style={{ marginTop: "var(--sp-6)" }}>
      <h6 style={{ fontSize: "var(--fs-sm)", color: "var(--text-secondary)", marginBottom: "var(--sp-3)" }}>
        Scene Analyses ({analyses.length})
      </h6>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--sp-4)" }}>
        {analyses.map((a) => {
          const isExpanded = expandedId === a.id;
          const pct = Math.round(a.confidence_score * 100);
          const color = pct >= 80 ? "var(--success)" : pct >= 50 ? "var(--warning)" : "var(--error)";
          
          return (
            <div key={a.id} style={{
              background: "rgba(19, 19, 31, 0.4)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-lg)",
              overflow: "hidden"
            }}>
              <div 
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "var(--sp-3) var(--sp-4)",
                  cursor: "pointer",
                  background: isExpanded ? "rgba(0, 0, 0, 0.2)" : "transparent"
                }}
                onClick={() => setExpandedId(isExpanded ? null : a.id)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-3)" }}>
                  <span style={{ fontSize: "1.2rem" }}>📸</span>
                  <div>
                    <div style={{ fontWeight: "var(--fw-medium)", fontSize: "var(--fs-sm)" }}>
                      Analysis with {a.model_used}
                    </div>
                    <div style={{ fontSize: "var(--fs-xs)", color: "var(--text-tertiary)" }}>
                      {timeAgo(a.created_at)}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-4)" }}>
                  <span style={{ fontSize: "var(--fs-xs)", color, fontWeight: "var(--fw-bold)" }}>
                    {pct}% Match
                  </span>
                  <span style={{ color: "var(--text-tertiary)", fontSize: "var(--fs-xs)" }}>
                    {isExpanded ? "▼" : "▶"}
                  </span>
                </div>
              </div>
              {isExpanded && (
                <div style={{ padding: "var(--sp-4)", borderTop: "1px solid var(--border-subtle)" }}>
                  <AnalysisResultComponent result={a.analysis_result} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
