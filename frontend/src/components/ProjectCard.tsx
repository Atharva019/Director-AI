"use client";

import React from "react";
import { useRouter } from "next/navigation";
import type { Project } from "@/types";
import styles from "./ProjectCard.module.css";

interface Props {
  project: Project;
  onEdit?: (project: Project) => void;
  onDelete?: (projectId: number) => void;
}

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

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export default function ProjectCard({ project, onEdit, onDelete }: Props) {
  const router = useRouter();

  return (
    <article
      className={`card card-interactive ${styles.card} animate-fade-in-up`}
      onClick={() => router.push(`/project/${project.id}`)}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && router.push(`/project/${project.id}`)}
    >
      {/* Action buttons – visible on hover */}
      {(onEdit || onDelete) && (
        <div className={styles.actions}>
          {onEdit && (
            <button
              className={styles.actionBtn}
              title="Edit project"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(project);
              }}
            >
              ✏️
            </button>
          )}
          {onDelete && (
            <button
              className={`${styles.actionBtn} ${styles.actionBtnDanger}`}
              title="Delete project"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(project.id);
              }}
            >
              🗑️
            </button>
          )}
        </div>
      )}

      {/* Header */}
      <div className={styles.header}>
        <h4 className={styles.title}>{project.title}</h4>
        <span className={`badge ${STATUS_BADGE[project.status] ?? "badge-gray"}`}>
          {STATUS_LABEL[project.status] ?? project.status}
        </span>
      </div>

      {/* Description */}
      {project.description && (
        <p className={`${styles.desc} text-secondary`}>
          {project.description}
        </p>
      )}

      {/* Meta row */}
      <div className={styles.meta}>
        <span className={`badge badge-blue`}>
          {project.genre}
        </span>
        <span className={styles.stat}>
          🎬 {project.scenes_count} scene{project.scenes_count !== 1 ? "s" : ""}
        </span>
        <span className={`${styles.time} text-tertiary`}>
          {timeAgo(project.updated_at)}
        </span>
      </div>
    </article>
  );
}

