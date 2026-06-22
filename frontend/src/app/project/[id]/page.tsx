"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import SceneCard from "@/components/SceneCard";
import { apiGet, apiPost, apiDel, apiPut } from "@/lib/api";
import type { Project, Scene, LocationType, TimeOfDay, ProjectStatus, Genre } from "@/types";
import styles from "./page.module.css";

const STATUS_BADGE: Record<string, string> = {
  draft: "badge-gray",
  in_production: "badge-amber",
  completed: "badge-green",
};

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  in_production: "In Production",
  completed: "Completed",
};

interface AddSceneForm {
  title: string;
  description: string;
  location_type: LocationType;
  time_of_day: TimeOfDay;
  mood: string;
  notes: string;
}

const DEFAULT_SCENE_FORM: AddSceneForm = {
  title: "",
  description: "",
  location_type: "interior",
  time_of_day: "day",
  mood: "",
  notes: "",
};

interface ProjectEditForm {
  title: string;
  description: string;
  genre: string;
  status: ProjectStatus;
}

function ProjectContent() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddScene, setShowAddScene] = useState(false);
  const [sceneForm, setSceneForm] = useState<AddSceneForm>(DEFAULT_SCENE_FORM);
  const [addingScene, setAddingScene] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Scene Edit state ──────────────────────────────────────────────────────
  const [editingScene, setEditingScene] = useState<Scene | null>(null);

  // ── Project Edit state ────────────────────────────────────────────────────
  const [showEditProject, setShowEditProject] = useState(false);
  const [projectForm, setProjectForm] = useState<ProjectEditForm>({
    title: "",
    description: "",
    genre: "",
    status: "draft",
  });
  const [savingProject, setSavingProject] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [proj, scns] = await Promise.all([
        apiGet<Project>(`/api/v1/projects/${projectId}`),
        apiGet<Scene[]>(`/api/v1/projects/${projectId}/scenes`),
      ]);
      setProject(proj);
      setScenes(scns);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDeleteProject = async () => {
    if (!confirm("Delete this project and all its scenes? This cannot be undone."))
      return;
    try {
      await apiDel(`/api/v1/projects/${projectId}`);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    }
  };

  // ── Project Edit handlers ─────────────────────────────────────────────────
  const handleOpenEditProject = () => {
    if (!project) return;
    setProjectForm({
      title: project.title,
      description: project.description ?? "",
      genre: project.genre,
      status: project.status,
    });
    setShowEditProject(true);
  };

  const handleSaveProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectForm.title.trim()) return;
    setSavingProject(true);
    try {
      const updated = await apiPut<Project>(`/api/v1/projects/${projectId}`, projectForm);
      setProject(updated);
      setShowEditProject(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSavingProject(false);
    }
  };

  // ── Scene Add / Edit handlers ─────────────────────────────────────────────
  const handleEditScene = (scene: Scene) => {
    setEditingScene(scene);
    setSceneForm({
      title: scene.title,
      description: scene.description ?? "",
      location_type: scene.location_type,
      time_of_day: scene.time_of_day,
      mood: scene.mood ?? "",
      notes: scene.notes ?? "",
    });
    setShowAddScene(true);
  };

  const handleCancelSceneForm = () => {
    setShowAddScene(false);
    setEditingScene(null);
    setSceneForm(DEFAULT_SCENE_FORM);
  };

  const handleAddScene = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sceneForm.title.trim()) return;
    setAddingScene(true);
    try {
      if (editingScene) {
        // ── Update existing scene ────────────────────────────────────────
        const updated = await apiPut<Scene>(
          `/api/v1/scenes/${editingScene.id}`,
          sceneForm
        );
        setScenes((prev) =>
          prev.map((s) => (s.id === updated.id ? updated : s))
        );
      } else {
        // ── Create new scene ─────────────────────────────────────────────
        const newScene = await apiPost<Scene>(
          `/api/v1/projects/${projectId}/scenes`,
          {
            ...sceneForm,
            scene_number: scenes.length + 1,
          }
        );
        setScenes((prev) => [...prev, newScene]);
      }
      setSceneForm(DEFAULT_SCENE_FORM);
      setShowAddScene(false);
      setEditingScene(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAddingScene(false);
    }
  };

  const handleDeleteScene = async (sceneId: number) => {
    if (!confirm("Delete this scene?")) return;
    try {
      await apiDel(`/api/v1/scenes/${sceneId}`);
      setScenes((prev) => prev.filter((s) => s.id !== sceneId));
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAnalyzeScene = (sceneId: number) => {
    router.push(`/analyze?sceneId=${sceneId}`);
  };

  if (loading) {
    return (
      <div className="page-wrapper">
        <Navbar />
        <div className="page-content container">
          <div className={styles.loadingWrap}>
            <div className="skeleton" style={{ height: 40, width: "40%", marginBottom: 16 }} />
            <div className="skeleton" style={{ height: 20, width: "60%", marginBottom: 32 }} />
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 140, marginBottom: 16 }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="page-wrapper">
        <Navbar />
        <div className="page-content container">
          <div className="empty-state">
            <div className="empty-state-icon">❌</div>
            <h4 className="empty-state-title">Project not found</h4>
            <a href="/dashboard" className="btn btn-primary mt-4">
              Back to Dashboard
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="page-content container">
        {/* Breadcrumb */}
        <nav className={styles.breadcrumb}>
          <a href="/dashboard" className={styles.breadcrumbLink}>
            Dashboard
          </a>
          <span className={styles.breadcrumbSep}>›</span>
          <span className={styles.breadcrumbCurrent}>{project.title}</span>
        </nav>

        {/* Project header */}
        <header className={`${styles.projectHeader} animate-fade-in-up`}>
          <div className={styles.headerInfo}>
            <div className={styles.headerTop}>
              <h2>{project.title}</h2>
              <div className={styles.headerBadges}>
                <span className={`badge ${STATUS_BADGE[project.status]}`}>
                  {STATUS_LABEL[project.status]}
                </span>
                <span className="badge badge-blue">{project.genre}</span>
              </div>
            </div>
            {project.description && (
              <p className="text-secondary mt-2">{project.description}</p>
            )}
          </div>
          <div className={styles.headerActions}>
            <button className="btn btn-ghost btn-sm" onClick={handleOpenEditProject}>
              ✏️ Edit
            </button>
            <button className="btn btn-danger btn-sm" onClick={handleDeleteProject}>
              🗑️ Delete
            </button>
          </div>
        </header>

        {/* Project Edit Form */}
        {showEditProject && (
          <form
            onSubmit={handleSaveProject}
            className={`card ${styles.addForm} animate-fade-in-up`}
          >
            <h5 className="mb-4">Edit Project</h5>
            <div className={styles.formGrid}>
              <div className="form-group">
                <label className="form-label">Title *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="Project title"
                  value={projectForm.title}
                  onChange={(e) =>
                    setProjectForm((f) => ({ ...f, title: e.target.value }))
                  }
                  required
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label">Genre</label>
                <select
                  className="select"
                  value={projectForm.genre}
                  onChange={(e) =>
                    setProjectForm((f) => ({ ...f, genre: e.target.value as Genre }))
                  }
                >
                  <option value="Drama">Drama</option>
                  <option value="Action">Action</option>
                  <option value="Comedy">Comedy</option>
                  <option value="Horror">Horror</option>
                  <option value="Thriller">Thriller</option>
                  <option value="Sci-Fi">Sci-Fi</option>
                  <option value="Documentary">Documentary</option>
                  <option value="Romance">Romance</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Status</label>
                <select
                  className="select"
                  value={projectForm.status}
                  onChange={(e) =>
                    setProjectForm((f) => ({
                      ...f,
                      status: e.target.value as ProjectStatus,
                    }))
                  }
                >
                  <option value="draft">Draft</option>
                  <option value="in_production">In Production</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>
            <div className="form-group mt-4">
              <label className="form-label">Description</label>
              <textarea
                className="textarea"
                placeholder="Project description…"
                value={projectForm.description}
                onChange={(e) =>
                  setProjectForm((f) => ({ ...f, description: e.target.value }))
                }
                rows={3}
              />
            </div>
            <div className={`${styles.formActions} mt-4`}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setShowEditProject(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={savingProject}
              >
                {savingProject ? <div className="spinner spinner-sm" /> : "Save Project"}
              </button>
            </div>
          </form>
        )}

        {error && (
          <div className={`card ${styles.errorBanner}`}>
            <p className="form-error">{error}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => setError(null)}>
              ✕
            </button>
          </div>
        )}

        {/* Scenes section */}
        <section className={styles.scenesSection}>
          <div className={styles.scenesHeader}>
            <h4>
              Scenes{" "}
              <span className="text-tertiary text-sm font-normal">
                ({scenes.length})
              </span>
            </h4>
            <button
              className="btn btn-primary"
              onClick={() => {
                if (showAddScene) {
                  handleCancelSceneForm();
                } else {
                  setEditingScene(null);
                  setSceneForm(DEFAULT_SCENE_FORM);
                  setShowAddScene(true);
                }
              }}
            >
              {showAddScene && !editingScene ? "✕ Cancel" : "+ Add Scene"}
            </button>
          </div>

          {/* Add / Edit scene form */}
          {showAddScene && (
            <form
              onSubmit={handleAddScene}
              className={`card ${styles.addForm} animate-fade-in-up`}
            >
              <h5 className="mb-4">{editingScene ? "Edit Scene" : "New Scene"}</h5>
              <div className={styles.formGrid}>
                <div className="form-group">
                  <label className="form-label">Title *</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Scene title"
                    value={sceneForm.title}
                    onChange={(e) =>
                      setSceneForm((f) => ({ ...f, title: e.target.value }))
                    }
                    required
                    autoFocus
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Location</label>
                  <select
                    className="select"
                    value={sceneForm.location_type}
                    onChange={(e) =>
                      setSceneForm((f) => ({
                        ...f,
                        location_type: e.target.value as LocationType,
                      }))
                    }
                  >
                    <option value="interior">Interior</option>
                    <option value="exterior">Exterior</option>
                    <option value="both">Both</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Time of Day</label>
                  <select
                    className="select"
                    value={sceneForm.time_of_day}
                    onChange={(e) =>
                      setSceneForm((f) => ({
                        ...f,
                        time_of_day: e.target.value as TimeOfDay,
                      }))
                    }
                  >
                    <option value="dawn">Dawn</option>
                    <option value="morning">Morning</option>
                    <option value="day">Day</option>
                    <option value="afternoon">Afternoon</option>
                    <option value="golden_hour">Golden Hour</option>
                    <option value="dusk">Dusk</option>
                    <option value="night">Night</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Mood</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g. Tense, Romantic"
                    value={sceneForm.mood}
                    onChange={(e) =>
                      setSceneForm((f) => ({ ...f, mood: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="form-group mt-4">
                <label className="form-label">Description</label>
                <textarea
                  className="textarea"
                  placeholder="Scene description…"
                  value={sceneForm.description}
                  onChange={(e) =>
                    setSceneForm((f) => ({ ...f, description: e.target.value }))
                  }
                  rows={3}
                />
              </div>
              <div className={`${styles.formActions} mt-4`}>
                {editingScene && (
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={handleCancelSceneForm}
                  >
                    Cancel
                  </button>
                )}
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={addingScene}
                >
                  {addingScene ? (
                    <div className="spinner spinner-sm" />
                  ) : editingScene ? (
                    "Save Scene"
                  ) : (
                    "Add Scene"
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Scene list */}
          {scenes.length === 0 && !showAddScene && (
            <div className="empty-state">
              <div className="empty-state-icon">🎬</div>
              <h4 className="empty-state-title">No scenes yet</h4>
              <p className="empty-state-desc">
                Start building your project by adding your first scene.
              </p>
            </div>
          )}

          <div className={`${styles.sceneList} stagger`}>
            {scenes.map((scene) => (
              <SceneCard
                key={scene.id}
                scene={scene}
                onEdit={handleEditScene}
                onDelete={handleDeleteScene}
                onAnalyze={handleAnalyzeScene}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default function ProjectDetailPage() {
  return (
    <AuthGuard>
      <ProjectContent />
    </AuthGuard>
  );
}
