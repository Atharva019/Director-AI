"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import ImageUploader from "@/components/ImageUploader";
import AnalysisResultComponent from "@/components/AnalysisResult";
import UpgradeModal from "@/components/UpgradeModal";
import UsageMeter from "@/components/UsageMeter";
import { apiUpload, apiGet, apiPost, QuotaError, isQuotaError } from "@/lib/api";
import type { SceneAnalysis, Project, Scene } from "@/types";
import styles from "./page.module.css";

const LOADING_MESSAGES = [
  "Analyzing lighting setup…",
  "Detecting camera position…",
  "Evaluating composition…",
  "Identifying color palette…",
  "Estimating lens parameters…",
  "Generating recommendations…",
];

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const sceneIdParam = searchParams.get("sceneId");

  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<SceneAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [quotaError, setQuotaError] = useState<QuotaError | null>(null);
  const [usageKey, setUsageKey] = useState(0);
  const [loadingMsg, setLoadingMsg] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [file]);

  // For "Save to Project" flow
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [selectedSceneId, setSelectedSceneId] = useState<string>(sceneIdParam ?? "");
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Cycle loading messages
  useEffect(() => {
    if (!analyzing) return;
    const iv = setInterval(() => {
      setLoadingMsg((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 2200);
    return () => clearInterval(iv);
  }, [analyzing]);

  // Fetch projects for save modal
  useEffect(() => {
    apiGet<Project[]>("/api/v1/projects")
      .then(setProjects)
      .catch(console.error);
  }, []);

  // Fetch scenes when project selected
  useEffect(() => {
    if (!selectedProjectId) {
      setScenes([]);
      setSelectedSceneId("");
      return;
    }
    apiGet<Scene[]>(`/api/v1/projects/${selectedProjectId}/scenes`)
      .then((data) => {
        setScenes(data);
        if (data.length > 0) {
          setSelectedSceneId((prev) =>
            data.some((s) => String(s.id) === prev) ? prev : String(data[0].id)
          );
        } else {
          setSelectedSceneId("");
        }
      })
      .catch(console.error);
  }, [selectedProjectId]);

  const handleAnalyze = async () => {
    if (!file) return;
    setError(null);
    setAnalyzing(true);
    setLoadingMsg(0);
    try {
      const result = await apiUpload<SceneAnalysis>(
        "/api/v1/analyze",
        file,
        sceneIdParam ? { scene_id: sceneIdParam } : undefined
      );
      setAnalysis(result);
      setUsageKey((k) => k + 1);
    } catch (err: any) {
      // Quota exhaustion gets the upgrade prompt, not a red error banner.
      if (isQuotaError(err)) {
        setQuotaError(err);
        setUsageKey((k) => k + 1);
      } else {
        setError(err.message ?? "Analysis failed");
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSaveToProject = () => {
    setShowSaveModal(true);
  };

  const handleNewAnalysis = () => {
    setFile(null);
    setAnalysis(null);
    setError(null);
  };

  const handleSave = async () => {
    if (!analysis || !selectedProjectId) return;
    setSaving(true);
    setSaveError(null);
    try {
      let targetSceneId = selectedSceneId;
      if (!targetSceneId) {
        if (scenes.length > 0) {
          targetSceneId = String(scenes[0].id);
        } else {
          const createdScene = await apiPost<Scene>(
            `/api/v1/projects/${selectedProjectId}/scenes`,
            {
              scene_number: 1,
              title: "Scene 1",
              location_type: "interior",
              time_of_day: "day",
              mood: analysis.analysis_result?.overall_mood || "Cinematic"
            }
          );
          targetSceneId = String(createdScene.id);
        }
      }

      await apiPost(`/api/v1/analyses/${analysis.id}/attach/${targetSceneId}`);
      setSaveSuccess(true);
      setTimeout(() => {
        setShowSaveModal(false);
        setSaveSuccess(false);
      }, 1200);
    } catch (err: any) {
      setSaveError(err.message ?? "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="page-content container container-md">
        <div className={`${styles.header} animate-fade-in-up`}>
          <h2>
            Scene <span className="text-gradient">Analysis</span>
          </h2>
          <p className="text-secondary mt-2">
            Upload a reference image and let AI analyze the cinematography — lighting, camera, composition, and mood.
          </p>
        </div>

        {/* Uploader */}
        <div className={`${styles.uploaderSection} animate-fade-in-up`}>
          <UsageMeter resource="analyses" refreshKey={usageKey} />

          <ImageUploader
            onFileSelected={setFile}
            disabled={analyzing}
          />

          <div className={styles.analyzeActions}>
            <button
              className="btn btn-primary btn-lg"
              disabled={!file || analyzing}
              onClick={handleAnalyze}
            >
              {analyzing ? (
                <>
                  <div className="spinner spinner-sm" />
                  Analyzing…
                </>
              ) : (
                "🔍 Analyze Image"
              )}
            </button>
          </div>
        </div>

        {/* Loading state */}
        {analyzing && (
          <div className={`${styles.loadingState} animate-fade-in`}>
            <div className={styles.loadingCard}>
              <div className="spinner" />
              <p className={styles.loadingMsg}>
                {LOADING_MESSAGES[loadingMsg]}
              </p>
              <div className={styles.loadingBar}>
                <div className={styles.loadingBarFill} />
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className={`card ${styles.errorCard} animate-fade-in`}>
            <p className="form-error">⚠️ {error}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => setError(null)}>
              Dismiss
            </button>
          </div>
        )}

        {/* Results */}
        {analysis && !analyzing && (
          <div className={`${styles.resultSection} animate-slide-up`}>
            <AnalysisResultComponent
              result={analysis.analysis_result}
              imageUrl={previewUrl ?? undefined}
              onSaveToProject={handleSaveToProject}
              onNewAnalysis={handleNewAnalysis}
            />
          </div>
        )}

        {/* Save modal */}
        {showSaveModal && (
          <div className={styles.modalOverlay} onClick={() => setShowSaveModal(false)}>
            <div
              className={`card ${styles.modal} animate-scale-in`}
              onClick={(e) => e.stopPropagation()}
            >
              <h4 className="mb-4">Save to Project</h4>
              <div className="form-group mb-4">
                <label className="form-label">Project</label>
                <select
                  className="select"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                >
                  <option value="">Select a project…</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title}
                    </option>
                  ))}
                </select>
              </div>
              {selectedProjectId && (
                scenes.length > 0 ? (
                  <div className="form-group mb-4">
                    <label className="form-label">Target Scene</label>
                    <select
                      className="select"
                      value={selectedSceneId}
                      onChange={(e) => setSelectedSceneId(e.target.value)}
                    >
                      {scenes.map((s) => (
                        <option key={s.id} value={s.id}>
                          Scene {s.scene_number}: {s.title}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <div className="mb-4 text-xs text-tertiary" style={{ background: "rgba(255, 255, 255, 0.04)", padding: "var(--sp-3)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                    ℹ️ This project has no scenes yet. A new <strong>Scene 1</strong> will be created automatically to attach this analysis.
                  </div>
                )
              )}
              <div className="flex justify-end gap-3">
                {saveSuccess && (
                  <span style={{ color: "var(--success)", alignSelf: "center", marginRight: "auto" }}>
                    ✅ Analysis saved to scene!
                  </span>
                )}
                {saveError && (
                  <span style={{ color: "var(--error)", alignSelf: "center", marginRight: "auto" }}>
                    ⚠️ {saveError}
                  </span>
                )}
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowSaveModal(false)}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  disabled={!selectedProjectId || saving || saveSuccess}
                  onClick={handleSave}
                >
                  {saving ? (
                    <>
                      <div className="spinner spinner-sm" />
                      Saving...
                    </>
                  ) : saveSuccess ? (
                    "Saved!"
                  ) : (
                    "💾 Save"
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <UpgradeModal error={quotaError} onClose={() => setQuotaError(null)} />
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <AuthGuard>
      <Suspense
        fallback={
          <div className="full-center">
            <div className="spinner" />
          </div>
        }
      >
        <AnalyzeContent />
      </Suspense>
    </AuthGuard>
  );
}
