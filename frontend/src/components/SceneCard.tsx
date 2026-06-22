"use client";

import React, { useState } from "react";
import { apiPost } from "@/lib/api";
import type { Scene, Shot, ShotType, CameraAngle, CameraMovement } from "@/types";
import ShotList from "./ShotList";
import SceneAnalyses from "./SceneAnalyses";
import styles from "./SceneCard.module.css";

interface Props {
  scene: Scene;
  onEdit?: (scene: Scene) => void;
  onDelete?: (sceneId: number) => void;
  onAnalyze?: (sceneId: number) => void;
}

const LOCATION_ICONS: Record<string, string> = {
  interior: "🏠",
  exterior: "🌲",
  both: "🏠🌲",
};

const TIME_LABELS: Record<string, string> = {
  dawn: "🌅 Dawn",
  morning: "☀️ Morning",
  day: "🌤️ Day",
  afternoon: "🌇 Afternoon",
  golden_hour: "✨ Golden Hour",
  dusk: "🌆 Dusk",
  night: "🌙 Night",
};

const SHOT_TYPES: { value: ShotType; label: string }[] = [
  { value: "wide", label: "Wide" },
  { value: "medium", label: "Medium" },
  { value: "close-up", label: "Close-up" },
  { value: "extreme_close-up", label: "Extreme Close-up" },
  { value: "over_the_shoulder", label: "Over the Shoulder" },
  { value: "pov", label: "POV" },
  { value: "aerial", label: "Aerial" },
  { value: "establishing", label: "Establishing" },
  { value: "insert", label: "Insert" },
  { value: "two_shot", label: "Two Shot" },
];

const CAMERA_ANGLES: { value: CameraAngle; label: string }[] = [
  { value: "eye_level", label: "Eye Level" },
  { value: "low_angle", label: "Low Angle" },
  { value: "high_angle", label: "High Angle" },
  { value: "dutch_angle", label: "Dutch Angle" },
  { value: "birds_eye", label: "Bird's Eye" },
  { value: "worms_eye", label: "Worm's Eye" },
];

const CAMERA_MOVEMENTS: { value: CameraMovement; label: string }[] = [
  { value: "static", label: "Static" },
  { value: "pan", label: "Pan" },
  { value: "tilt", label: "Tilt" },
  { value: "dolly", label: "Dolly" },
  { value: "tracking", label: "Tracking" },
  { value: "crane", label: "Crane" },
  { value: "handheld", label: "Handheld" },
  { value: "steadicam", label: "Steadicam" },
  { value: "zoom", label: "Zoom" },
];

interface ShotFormData {
  shot_type: ShotType;
  camera_angle: CameraAngle;
  camera_movement: CameraMovement;
  lens_mm: string;
  description: string;
  notes: string;
}

const DEFAULT_SHOT_FORM: ShotFormData = {
  shot_type: "wide",
  camera_angle: "eye_level",
  camera_movement: "static",
  lens_mm: "",
  description: "",
  notes: "",
};

export default function SceneCard({ scene, onEdit, onDelete, onAnalyze }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [showShotForm, setShowShotForm] = useState(false);
  const [shotForm, setShotForm] = useState<ShotFormData>(DEFAULT_SHOT_FORM);
  const [addingShot, setAddingShot] = useState(false);
  const [shotError, setShotError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleAddShot = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddingShot(true);
    setShotError(null);
    try {
      await apiPost<Shot>(
        `/api/v1/scenes/${scene.id}/shots`,
        {
          shot_type: shotForm.shot_type,
          camera_angle: shotForm.camera_angle,
          camera_movement: shotForm.camera_movement,
          lens_mm: shotForm.lens_mm ? parseInt(shotForm.lens_mm, 10) : null,
          description: shotForm.description || null,
          notes: shotForm.notes || null,
        }
      );
      setShotForm(DEFAULT_SHOT_FORM);
      setShowShotForm(false);
      setRefreshKey((k) => k + 1);
      // Auto-expand shots to show the new one
      setExpanded(true);
    } catch (err: any) {
      setShotError(err.message);
    } finally {
      setAddingShot(false);
    }
  };

  return (
    <article className={`card ${styles.card} animate-fade-in-up`}>
      {/* Header row */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={`badge badge-amber ${styles.sceneNum}`}>
            Scene {scene.scene_number}
          </span>
          <h5 className={styles.title}>{scene.title}</h5>
        </div>
        <div className={styles.actions}>
          {onAnalyze && (
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => onAnalyze(scene.id)}
              title="Analyze Scene"
            >
              🔍
            </button>
          )}
          {onEdit && (
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => onEdit(scene)}
              title="Edit Scene"
            >
              ✏️
            </button>
          )}
          {onDelete && (
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => onDelete(scene.id)}
              title="Delete Scene"
            >
              🗑️
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      {scene.description && (
        <p className={`${styles.desc} text-secondary`}>{scene.description}</p>
      )}

      {/* Tags row */}
      <div className={styles.tags}>
        <span className={`badge badge-gray`}>
          {LOCATION_ICONS[scene.location_type] ?? "📍"} {scene.location_type}
        </span>
        <span className={`badge badge-gray`}>
          {TIME_LABELS[scene.time_of_day] ?? scene.time_of_day}
        </span>
        {scene.mood && (
          <span className="badge badge-blue">
            {scene.mood}
          </span>
        )}
        <span className={`${styles.shotCount} text-tertiary text-sm`}>
          🎥 {scene.shots_count} shot{scene.shots_count !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Notes */}
      {scene.notes && (
        <p className={`${styles.notes} text-tertiary text-sm`}>
          💬 {scene.notes}
        </p>
      )}

      {/* Expand shots */}
      <div className={styles.expandRow}>
        <button
          className={`btn btn-ghost btn-sm ${styles.expandBtn}`}
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "▲ Hide Shots" : "▼ Show Shots"}
        </button>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => {
            setShowShotForm((v) => !v);
            if (!showShotForm) setExpanded(true);
          }}
        >
          {showShotForm ? "✕ Cancel" : "+ Add Shot"}
        </button>
      </div>

      {/* Inline Add Shot Form */}
      {showShotForm && (
        <form
          onSubmit={handleAddShot}
          className={`${styles.shotForm} animate-fade-in-up`}
        >
          <h6 className={styles.shotFormTitle}>New Shot</h6>
          {shotError && (
            <p className="form-error" style={{ marginBottom: 8 }}>{shotError}</p>
          )}
          <div className={styles.shotFormGrid}>
            <div className="form-group">
              <label className="form-label">Shot Type</label>
              <select
                className="select"
                value={shotForm.shot_type}
                onChange={(e) =>
                  setShotForm((f) => ({ ...f, shot_type: e.target.value as ShotType }))
                }
              >
                {SHOT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Camera Angle</label>
              <select
                className="select"
                value={shotForm.camera_angle}
                onChange={(e) =>
                  setShotForm((f) => ({ ...f, camera_angle: e.target.value as CameraAngle }))
                }
              >
                {CAMERA_ANGLES.map((a) => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Camera Movement</label>
              <select
                className="select"
                value={shotForm.camera_movement}
                onChange={(e) =>
                  setShotForm((f) => ({ ...f, camera_movement: e.target.value as CameraMovement }))
                }
              >
                {CAMERA_MOVEMENTS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Lens (mm)</label>
              <input
                type="number"
                className="input"
                placeholder="e.g. 50"
                value={shotForm.lens_mm}
                onChange={(e) =>
                  setShotForm((f) => ({ ...f, lens_mm: e.target.value }))
                }
                min={1}
              />
            </div>
          </div>
          <div className="form-group" style={{ marginTop: 12 }}>
            <label className="form-label">Description</label>
            <textarea
              className="textarea"
              placeholder="Shot description…"
              value={shotForm.description}
              onChange={(e) =>
                setShotForm((f) => ({ ...f, description: e.target.value }))
              }
              rows={2}
            />
          </div>
          <div className="form-group" style={{ marginTop: 8 }}>
            <label className="form-label">Notes</label>
            <textarea
              className="textarea"
              placeholder="Director's notes…"
              value={shotForm.notes}
              onChange={(e) =>
                setShotForm((f) => ({ ...f, notes: e.target.value }))
              }
              rows={2}
            />
          </div>
          <div className={styles.shotFormActions}>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setShowShotForm(false);
                setShotForm(DEFAULT_SHOT_FORM);
                setShotError(null);
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={addingShot}
            >
              {addingShot ? <div className="spinner spinner-sm" /> : "Add Shot"}
            </button>
          </div>
        </form>
      )}

      {expanded && (
        <div className={styles.shotsContainer}>
          <SceneAnalyses sceneId={scene.id} />
          <ShotList sceneId={scene.id} refreshKey={refreshKey} />
        </div>
      )}
    </article>
  );
}
