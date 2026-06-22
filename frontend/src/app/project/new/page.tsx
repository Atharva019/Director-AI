"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import { apiPost } from "@/lib/api";
import type { Project, Genre } from "@/types";
import styles from "./page.module.css";

const GENRES: Genre[] = [
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

function NewProjectContent() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [genre, setGenre] = useState<string>("Drama");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const project = await apiPost<Project>("/api/v1/projects", {
        title: title.trim(),
        description: description.trim() || null,
        genre,
        status: "draft",
      });
      router.push(`/project/${project.id}`);
    } catch (err: any) {
      setError(err.message ?? "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="page-content container container-sm">
        {/* Breadcrumb */}
        <nav className={styles.breadcrumb}>
          <a href="/dashboard" className={styles.breadcrumbLink}>
            Dashboard
          </a>
          <span className={styles.breadcrumbSep}>›</span>
          <span className={styles.breadcrumbCurrent}>New Project</span>
        </nav>

        <div className={`card ${styles.formCard} animate-fade-in-up`}>
          <h3 className={styles.heading}>Create New Project</h3>
          <p className="text-secondary text-sm mb-6">
            Set up your filmmaking project with basic details. You can add scenes and shots later.
          </p>

          <form onSubmit={handleSubmit} className={styles.form}>
            <div className="form-group">
              <label className="form-label" htmlFor="title">
                Project Title *
              </label>
              <input
                id="title"
                type="text"
                className="input"
                placeholder="e.g. The Last Sunset"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="desc">
                Description
              </label>
              <textarea
                id="desc"
                className="textarea"
                placeholder="Brief synopsis or notes about the project…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="genre">
                Genre
              </label>
              <select
                id="genre"
                className="select"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
              >
                {GENRES.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </div>

            {error && <p className="form-error">{error}</p>}

            <div className={styles.actions}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => router.back()}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary btn-lg"
                disabled={submitting}
              >
                {submitting ? (
                  <div className="spinner spinner-sm" />
                ) : (
                  "🎬 Create Project"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function NewProjectPage() {
  return (
    <AuthGuard>
      <NewProjectContent />
    </AuthGuard>
  );
}
