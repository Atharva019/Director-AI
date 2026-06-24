"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import ProjectCard from "@/components/ProjectCard";
import { apiGet, apiPut, apiDel } from "@/lib/api";
import type { Project, Genre, ProjectStatus, SceneAnalysis } from "@/types";
import styles from "./page.module.css";

const GENRE_OPTIONS: Genre[] = [
  "Drama",
  "Action",
  "Comedy",
  "Horror",
  "Thriller",
  "Sci-Fi",
  "Documentary",
  "Romance",
  "Other",
];

const STATUS_OPTIONS: { value: ProjectStatus; label: string }[] = [
  { value: "draft", label: "Draft" },
  { value: "in_production", label: "In Production" },
  { value: "completed", label: "Completed" },
];

function DashboardContent() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [genreFilter, setGenreFilter] = useState<string>("all");

  const [recentAnalyses, setRecentAnalyses] = useState<SceneAnalysis[]>([]);
  const [analysesLoading, setAnalysesLoading] = useState(true);

  // ── Edit modal state ──────────────────────────────────────────────────────
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [editForm, setEditForm] = useState({
    title: "",
    description: "",
    genre: "Drama" as Genre | string,
    status: "draft" as ProjectStatus,
  });
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Project[]>("/api/v1/projects")
      .then(setProjects)
      .catch(console.error)
      .finally(() => setLoading(false));

    apiGet<SceneAnalysis[]>("/api/v1/analyses")
      .then((data) => {
        // Backend returns items or maybe just array
        const items = Array.isArray(data) ? data : (data as any).items || [];
        setRecentAnalyses(items.slice(0, 5));
      })
      .catch(console.error)
      .finally(() => setAnalysesLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let result = projects;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.genre.toLowerCase().includes(q)
      );
    }
    if (statusFilter !== "all") {
      result = result.filter((p) => p.status === statusFilter);
    }
    if (genreFilter !== "all") {
      result = result.filter((p) => p.genre === genreFilter);
    }
    return result;
  }, [projects, search, statusFilter, genreFilter]);

  // ── Edit handlers ─────────────────────────────────────────────────────────
  const handleEditOpen = useCallback((project: Project) => {
    setEditingProject(project);
    setEditForm({
      title: project.title,
      description: project.description ?? "",
      genre: project.genre,
      status: project.status,
    });
    setEditError(null);
  }, []);

  const handleEditClose = useCallback(() => {
    setEditingProject(null);
    setEditError(null);
  }, []);

  const handleEditSave = useCallback(async () => {
    if (!editingProject) return;
    if (!editForm.title.trim()) {
      setEditError("Title is required.");
      return;
    }
    setEditSaving(true);
    setEditError(null);
    try {
      const updated = await apiPut<Project>(
        `/api/v1/projects/${editingProject.id}`,
        {
          title: editForm.title.trim(),
          description: editForm.description.trim() || null,
          genre: editForm.genre,
          status: editForm.status,
        }
      );
      setProjects((prev) =>
        prev.map((p) => (p.id === updated.id ? updated : p))
      );
      setEditingProject(null);
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : "Failed to update project.");
    } finally {
      setEditSaving(false);
    }
  }, [editingProject, editForm]);

  // ── Delete handler ────────────────────────────────────────────────────────
  const handleDelete = useCallback(async (projectId: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this project? This action cannot be undone."
    );
    if (!confirmed) return;

    try {
      await apiDel(`/api/v1/projects/${projectId}`);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete project.");
    }
  }, []);

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="page-content container">
        <div className={styles.layout}>
          {/* Main Content */}
          <div className={styles.mainContent}>
            {/* Header */}
            <div className={styles.header}>
              <div>
                <h2 className={styles.title}>Your Projects</h2>
                <p className="text-secondary text-sm">
                  {projects.length} project{projects.length !== 1 ? "s" : ""}
                </p>
              </div>
              <Link href="/project/new" className="btn btn-primary btn-lg">
                ✨ New Project
              </Link>
            </div>

            {/* Search / Filter */}
            <div className={styles.toolbar}>
              <div className={styles.searchWrap}>
                <span className={styles.searchIcon}>🔍</span>
                <input
                  type="text"
                  className={`input ${styles.searchInput}`}
                  placeholder="Search projects…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className={styles.filtersWrap}>
                <select
                  className={`select ${styles.filter}`}
                  value={genreFilter}
                  onChange={(e) => setGenreFilter(e.target.value)}
                >
                  <option value="all">All Genres</option>
                  {GENRE_OPTIONS.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
                <select
                  className={`select ${styles.filter}`}
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Status</option>
                  <option value="draft">Draft</option>
                  <option value="in_production">In Production</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>

            {/* Loading skeletons */}
            {loading && (
              <div className={`grid grid-cols-3 ${styles.grid}`}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="skeleton skeleton-card" />
                ))}
              </div>
            )}

            {/* Empty state */}
            {!loading && filtered.length === 0 && (
              <div className="empty-state animate-fade-in">
                <div className="empty-state-icon">🎬</div>
                <h4 className="empty-state-title">
                  {search || statusFilter !== "all" || genreFilter !== "all"
                    ? "No matching projects"
                    : "Create your first project"}
                </h4>
                <p className="empty-state-desc">
                  {search || statusFilter !== "all" || genreFilter !== "all"
                    ? "Try adjusting your search or filters."
                    : "Start by creating a new filmmaking project. You'll be able to add scenes, plan shots, and analyze cinematography."}
                </p>
                {!search && statusFilter === "all" && genreFilter === "all" && (
                  <Link href="/project/new" className="btn btn-primary btn-lg mt-4">
                    ✨ Create Project
                  </Link>
                )}
              </div>
            )}

            {/* Project grid */}
            {!loading && filtered.length > 0 && (
              <div className={`grid grid-cols-3 stagger ${styles.grid}`}>
                {filtered.map((p) => (
                  <ProjectCard
                    key={p.id}
                    project={p}
                    onEdit={handleEditOpen}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <aside className={styles.sidebar}>
            <div className={styles.sidebarHeader}>
              <h3 className={styles.sidebarTitle}>Recent Analyses</h3>
              <Link href="/history" className={styles.viewAllLink}>
                View all
              </Link>
            </div>
            
            <div className={styles.sidebarContent}>
              {analysesLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className={`skeleton ${styles.miniCardSkeleton}`} />
                ))
              ) : recentAnalyses.length === 0 ? (
                <div className={styles.emptySidebar}>
                  <p className="text-secondary text-sm">No analyses yet.</p>
                  <Link href="/analyze" className="btn btn-ghost btn-sm mt-2">
                    Analyze Image
                  </Link>
                </div>
              ) : (
                <div className={styles.miniCardList}>
                  {recentAnalyses.map((analysis) => (
                    <Link
                      key={analysis.id}
                      href="/history"
                      className={styles.miniCard}
                    >
                      <div className={styles.miniCardThumb}>
                        {analysis.image_path ? (
                          <img
                            src={`/api/v1${analysis.image_path}`}
                            alt="Analysis thumbnail"
                            className={styles.thumbImg}
                          />
                        ) : (
                          <div className={styles.thumbPlaceholder}>📷</div>
                        )}
                      </div>
                      <div className={styles.miniCardInfo}>
                        <h4 className={styles.miniCardMood}>
                          {analysis.analysis_result.overall_mood || "Analysis"}
                        </h4>
                        <p className={styles.miniCardDate}>
                          {new Date(analysis.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                          })}
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>

      {/* ── Edit Project Modal ─────────────────────────────────────────────── */}
      {editingProject && (
        <div className={styles.modalOverlay} onClick={handleEditClose}>
          <div
            className={styles.modal}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Edit Project</h3>
              <button
                className={styles.modalClose}
                onClick={handleEditClose}
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            <div className={styles.modalBody}>
              {editError && (
                <p className={styles.modalError}>{editError}</p>
              )}

              <label className={styles.fieldLabel}>
                Title
                <input
                  type="text"
                  className="input"
                  value={editForm.title}
                  onChange={(e) =>
                    setEditForm((f) => ({ ...f, title: e.target.value }))
                  }
                />
              </label>

              <label className={styles.fieldLabel}>
                Description
                <textarea
                  className={`input ${styles.textarea}`}
                  rows={3}
                  value={editForm.description}
                  onChange={(e) =>
                    setEditForm((f) => ({ ...f, description: e.target.value }))
                  }
                />
              </label>

              <div className={styles.fieldRow}>
                <label className={styles.fieldLabel}>
                  Genre
                  <select
                    className="select"
                    value={editForm.genre}
                    onChange={(e) =>
                      setEditForm((f) => ({ ...f, genre: e.target.value }))
                    }
                  >
                    {GENRE_OPTIONS.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </label>

                <label className={styles.fieldLabel}>
                  Status
                  <select
                    className="select"
                    value={editForm.status}
                    onChange={(e) =>
                      setEditForm((f) => ({
                        ...f,
                        status: e.target.value as ProjectStatus,
                      }))
                    }
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>

            <div className={styles.modalFooter}>
              <button
                className="btn btn-ghost"
                onClick={handleEditClose}
                disabled={editSaving}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleEditSave}
                disabled={editSaving}
              >
                {editSaving ? "Saving…" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  );
}
