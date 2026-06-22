"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import ImageUploader from "@/components/ImageUploader";
import AnalysisResultComponent from "@/components/AnalysisResult";
import { apiUpload, apiGet, apiPost } from "@/lib/api";
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
  const [loadingMsg, setLoadingMsg] = useState(0);

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
      return;
    }
    apiGet<Scene[]>(`/api/v1/projects/${selectedProjectId}/scenes`)
      .then(setScenes)
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
    } catch (err: any) {
      setError(err.message ?? "Analysis failed");
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
    if (!analysis) return;
    setSaving(true);
    setSaveError(null);
    try {
      await apiPost(`/api/v1/analyses/${analysis.id}/attach/${selectedSceneId}`);
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
              {scenes.length > 0 && (
                <div className="form-group mb-4">
                  <label className="form-label">Scene (optional)</label>
                  <select
                    className="select"
                    value={selectedSceneId}
                    onChange={(e) => setSelectedSceneId(e.target.value)}
                  >
                    <option value="">No specific scene</option>
                    {scenes.map((s) => (
                      <option key={s.id} value={s.id}>
                        Scene {s.scene_number}: {s.title}
                      </option>
                    ))}
                  </select>
                </div>
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
