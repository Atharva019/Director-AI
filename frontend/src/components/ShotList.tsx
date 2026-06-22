"use client";

import React, { useEffect, useState } from "react";
import { apiGet, apiPut, apiDel } from "@/lib/api";
import type { Shot, ShotType, CameraAngle, CameraMovement } from "@/types";
import styles from "./ShotList.module.css";

interface Props {
  sceneId: number;
  shots?: Shot[];
  refreshKey?: number;
}

const SHOT_ICONS: Record<string, string> = {
  wide: "🌄",
  medium: "🧑",
  "close-up": "👁️",
  "extreme_close-up": "🔬",
  over_the_shoulder: "🫂",
  pov: "👀",
  aerial: "🦅",
  establishing: "🏙️",
  insert: "🔎",
  two_shot: "👥",
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

interface ShotEditForm {
  shot_type: ShotType;
  camera_angle: CameraAngle;
  camera_movement: CameraMovement;
  lens_mm: string;
  description: string;
  notes: string;
}

export default function ShotList({ sceneId, shots: propShots, refreshKey }: Props) {
  const [shots, setShots] = useState<Shot[]>(propShots ?? []);
  const [loading, setLoading] = useState(!propShots);
  const [editingShotId, setEditingShotId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<ShotEditForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  useEffect(() => {
    if (propShots) return;
    setLoading(true);
    apiGet<Shot[]>(`/api/v1/scenes/${sceneId}/shots`)
      .then(setShots)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sceneId, propShots, refreshKey]);

  const handleStartEdit = (shot: Shot) => {
    setEditingShotId(shot.id);
    setEditError(null);
    setEditForm({
      shot_type: shot.shot_type as ShotType,
      camera_angle: shot.camera_angle as CameraAngle,
      camera_movement: shot.camera_movement as CameraMovement,
      lens_mm: shot.lens_mm ? String(shot.lens_mm) : "",
      description: shot.description ?? "",
      notes: shot.notes ?? "",
    });
  };

  const handleCancelEdit = () => {
    setEditingShotId(null);
    setEditForm(null);
    setEditError(null);
  };

  const handleSaveEdit = async (shotId: number) => {
    if (!editForm) return;
    setSaving(true);
    setEditError(null);
    try {
      const updated = await apiPut<Shot>(`/api/v1/shots/${shotId}`, {
        shot_type: editForm.shot_type,
        camera_angle: editForm.camera_angle,
        camera_movement: editForm.camera_movement,
        lens_mm: editForm.lens_mm ? parseInt(editForm.lens_mm, 10) : null,
        description: editForm.description || null,
        notes: editForm.notes || null,
      });
      setShots((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
      setEditingShotId(null);
      setEditForm(null);
    } catch (err: any) {
      setEditError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteShot = async (shotId: number) => {
    if (!confirm("Delete this shot?")) return;
    try {
      await apiDel(`/api/v1/shots/${shotId}`);
      setShots((prev) => prev.filter((s) => s.id !== shotId));
    } catch (err: any) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className="spinner spinner-sm" />
        <span className="text-tertiary text-sm">Loading shots…</span>
      </div>
    );
  }

  if (shots.length === 0) {
    return (
      <div className={styles.empty}>
        <span className="text-tertiary text-sm">No shots yet — add your first shot above.</span>
      </div>
    );
  }

  return (
    <ol className={styles.list}>
      {shots.map((shot) => (
        <li key={shot.id} className={styles.item}>
          {editingShotId === shot.id && editForm ? (
            /* ── Inline Edit Form ──────────────────────────────────────── */
            <div className={styles.editFormWrap}>
              {editError && (
                <p className="form-error" style={{ marginBottom: 8 }}>{editError}</p>
              )}
              <div className={styles.editGrid}>
                <div className="form-group">
                  <label className="form-label">Shot Type</label>
                  <select
                    className="select"
                    value={editForm.shot_type}
                    onChange={(e) =>
                      setEditForm((f) => f && ({ ...f, shot_type: e.target.value as ShotType }))
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
                    value={editForm.camera_angle}
                    onChange={(e) =>
                      setEditForm((f) => f && ({ ...f, camera_angle: e.target.value as CameraAngle }))
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
                    value={editForm.camera_movement}
                    onChange={(e) =>
                      setEditForm((f) => f && ({ ...f, camera_movement: e.target.value as CameraMovement }))
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
                    value={editForm.lens_mm}
                    onChange={(e) =>
                      setEditForm((f) => f && ({ ...f, lens_mm: e.target.value }))
                    }
                    min={1}
                  />
                </div>
              </div>
              <div className="form-group" style={{ marginTop: 8 }}>
                <label className="form-label">Description</label>
                <textarea
                  className="textarea"
                  placeholder="Shot description…"
                  value={editForm.description}
                  onChange={(e) =>
                    setEditForm((f) => f && ({ ...f, description: e.target.value }))
                  }
                  rows={2}
                />
              </div>
              <div className="form-group" style={{ marginTop: 8 }}>
                <label className="form-label">Notes</label>
                <textarea
                  className="textarea"
                  placeholder="Director's notes…"
                  value={editForm.notes}
                  onChange={(e) =>
                    setEditForm((f) => f && ({ ...f, notes: e.target.value }))
                  }
                  rows={2}
                />
              </div>
              <div className={styles.editActions}>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={handleCancelEdit}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleSaveEdit(shot.id)}
                  disabled={saving}
                >
                  {saving ? <div className="spinner spinner-sm" /> : "Save"}
                </button>
              </div>
            </div>
          ) : (
            /* ── Normal Shot Display ───────────────────────────────────── */
            <>
              <div className={styles.number}>
                <span className={styles.numBadge}>{shot.shot_number}</span>
              </div>
              <div className={styles.content}>
                <div className={styles.row}>
                  <span className={styles.type}>
                    {SHOT_ICONS[shot.shot_type] ?? "🎥"} {shot.shot_type.replace(/_/g, " ")}
                  </span>
                  <span className={`${styles.meta} text-tertiary`}>
                    {shot.camera_angle.replace(/_/g, " ")}
                  </span>
                  {shot.camera_movement !== "static" && (
                    <span className={`badge badge-blue ${styles.metaBadge}`}>
                      {shot.camera_movement}
                    </span>
                  )}
                  {shot.lens_mm && (
                    <span className={`${styles.meta} text-tertiary`}>
                      {shot.lens_mm}mm
                    </span>
                  )}
                </div>
                {shot.description && (
                  <p className={`${styles.desc} text-secondary text-sm`}>
                    {shot.description}
                  </p>
                )}
                {shot.notes && (
                  <p className={`${styles.shotNotes} text-tertiary text-sm`}>
                    💬 {shot.notes}
                  </p>
                )}
              </div>
              <div className={styles.shotActions}>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => handleStartEdit(shot)}
                  title="Edit Shot"
                >
                  ✏️
                </button>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => handleDeleteShot(shot.id)}
                  title="Delete Shot"
                >
                  🗑️
                </button>
              </div>
            </>
          )}
        </li>
      ))}
    </ol>
  );
}
