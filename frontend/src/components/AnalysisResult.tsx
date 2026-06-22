"use client";
 
import React, { useState } from "react";
import type { AnalysisResult as AnalysisResultType } from "@/types";
import styles from "./AnalysisResult.module.css";
 
interface Props {
  result: AnalysisResultType;
  onSaveToProject?: () => void;
  onNewAnalysis?: () => void;
}
 
type Tab = "lighting" | "camera" | "composition" | "mood" | "recommendations";
 
const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "lighting", label: "Lighting", icon: "💡" },
  { key: "camera", label: "Camera", icon: "📷" },
  { key: "composition", label: "Composition", icon: "🖼️" },
  { key: "mood", label: "Mood & Color", icon: "🎨" },
  { key: "recommendations", label: "Tips", icon: "⭐" },
];
 
function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? "var(--success)" : pct >= 50 ? "var(--warning)" : "var(--error)";
  return (
    <div className={styles.confidence}>
      <div className={styles.confLabel}>
        <span className="text-sm font-medium">Confidence</span>
        <span className="text-sm font-semibold" style={{ color }}>
          {pct}%
        </span>
      </div>
      <div className={styles.confTrack}>
        <div
          className={styles.confFill}
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}
 
function SpecCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: string;
}) {
  return (
    <div className={styles.spec}>
      {icon && <span className={styles.specIcon}>{icon}</span>}
      <span className={`${styles.specValue} font-semibold`}>{value}</span>
      <span className={`${styles.specLabel} text-tertiary text-xs`}>
        {label}
      </span>
    </div>
  );
}

/**
 * Safely normalizes value into a string array.
 * Handles strings (including markdown lists and JSON arrays), arrays, and fallback/empty values.
 */
function ensureArray(val: any): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed.startsWith("[")) {
      try {
        const parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed)) {
          return parsed.map(String);
        }
      } catch {}
    }
    if (val.includes("\n")) {
      return val
        .split("\n")
        .map((s) => s.replace(/^[-*•\d.\s+]+/g, "").trim())
        .filter(Boolean);
    }
    return [val];
  }
  return [String(val)];
}
 
export default function AnalysisResult({ result, onSaveToProject, onNewAnalysis }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("lighting");

  const compositionRules = ensureArray(result.composition_rules);
  const dominantColors = ensureArray(result.dominant_colors);
  const recommendedEquipment = ensureArray(result.recommended_equipment);
  const setupInstructions = ensureArray(result.setup_instructions);
  const tips = ensureArray(result.tips);
 
  return (
    <div className={`${styles.wrapper} animate-fade-in-up`}>
      {/* Confidence */}
      <ConfidenceBar score={result.confidence_score} />
 
      {/* Tabs */}
      <div className={styles.tabs}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`${styles.tab} ${activeTab === tab.key ? styles.tabActive : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <span>{tab.icon}</span>
            <span className="hide-mobile">{tab.label}</span>
          </button>
        ))}
      </div>
 
      {/* Tab content */}
      <div className={styles.content}>
        {/* ── Lighting ───────────────────────────────────── */}
        {activeTab === "lighting" && (
          <div className={`${styles.panel} animate-fade-in`}>
            <div className={styles.specGrid}>
              <SpecCard label="Lighting Style" value={result.lighting_style} icon="💡" />
              <SpecCard label="Color Temperature" value={result.color_temperature} icon="🌡️" />
              <SpecCard label="Lighting Ratio" value={result.lighting_ratio} icon="⚖️" />
            </div>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Setup Description</h6>
              <p className="text-secondary">{result.lighting_setup}</p>
            </div>
          </div>
        )}
 
        {/* ── Camera ─────────────────────────────────────── */}
        {activeTab === "camera" && (
          <div className={`${styles.panel} animate-fade-in`}>
            <div className={styles.specGrid}>
              <SpecCard label="Focal Length" value={result.estimated_focal_length} icon="🔭" />
              <SpecCard label="Aperture" value={result.estimated_aperture} icon="📸" />
              <SpecCard label="Depth of Field" value={result.depth_of_field} icon="🎯" />
              <SpecCard label="Camera Height" value={result.camera_height} icon="📐" />
              <SpecCard label="Camera Angle" value={result.camera_angle} icon="📷" />
            </div>
          </div>
        )}
 
        {/* ── Composition ────────────────────────────────── */}
        {activeTab === "composition" && (
          <div className={`${styles.panel} animate-fade-in`}>
            <div className={styles.specGrid}>
              <SpecCard label="Framing" value={result.framing} icon="🖼️" />
              <SpecCard label="Aspect Ratio" value={result.aspect_ratio} icon="📐" />
            </div>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Composition Rules</h6>
              <div className={styles.chipList}>
                {compositionRules.map((rule, i) => (
                  <span key={i} className="badge badge-amber">
                    {rule}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
 
        {/* ── Mood & Color ───────────────────────────────── */}
        {activeTab === "mood" && (
          <div className={`${styles.panel} animate-fade-in`}>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Overall Mood</h6>
              <p className={styles.moodText}>{result.overall_mood}</p>
            </div>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Color Palette Mood</h6>
              <p className="text-secondary">{result.color_palette_mood}</p>
            </div>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Dominant Colors</h6>
              <div className={styles.colorSwatches}>
                {dominantColors.map((color, i) => (
                  <div key={i} className={styles.swatch}>
                    <div
                      className={styles.swatchColor}
                      style={{
                        background: color.startsWith("#") ? color : undefined,
                      }}
                    />
                    <span className="text-xs text-tertiary">{color}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
 
        {/* ── Recommendations ────────────────────────────── */}
        {activeTab === "recommendations" && (
          <div className={`${styles.panel} animate-fade-in`}>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Recommended Equipment</h6>
              <ul className={styles.recList}>
                {recommendedEquipment.map((eq, i) => (
                  <li key={i} className={styles.recItem}>
                    <span className={styles.recBullet}>🔹</span>
                    {eq}
                  </li>
                ))}
              </ul>
            </div>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Setup Instructions</h6>
              <ol className={styles.recListNumbered}>
                {setupInstructions.map((step, i) => (
                  <li key={i} className={styles.recItem}>
                    <span className={styles.stepNum}>{i + 1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
            <div className={styles.section}>
              <h6 className={styles.sectionTitle}>Pro Tips</h6>
              <ul className={styles.recList}>
                {tips.map((tip, i) => (
                  <li key={i} className={styles.recItem}>
                    <span className={styles.recBullet}>💡</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
 
      {/* Save button */}
      {(onSaveToProject || onNewAnalysis) && (
        <div className={styles.footer}>
          {onNewAnalysis && (
            <button className="btn btn-secondary btn-lg" onClick={onNewAnalysis}>
              🔄 New Analysis
            </button>
          )}
          {onSaveToProject && (
            <button className="btn btn-primary btn-lg" onClick={onSaveToProject}>
              💾 Save to Project
            </button>
          )}
        </div>
      )}
    </div>
  );
}
