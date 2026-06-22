"use client";

import React, { useRef, useState, useCallback } from "react";
import styles from "./ImageUploader.module.css";

interface Props {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

export default function ImageUploader({ onFileSelected, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      if (!ACCEPTED.includes(file.type)) {
        setError("Please upload a JPG, PNG, or WebP image.");
        return;
      }
      if (file.size > MAX_SIZE) {
        setError("File is too large. Maximum size is 10 MB.");
        return;
      }
      setFileName(file.name);
      const url = URL.createObjectURL(file);
      setPreview(url);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleRemove = () => {
    setPreview(null);
    setFileName(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className={styles.wrapper}>
      {!preview ? (
        <div
          className={`${styles.dropzone} ${dragOver ? styles.dragActive : ""} ${disabled ? styles.disabled : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && !disabled && inputRef.current?.click()}
        >
          <div className={styles.dropContent}>
            <div className={styles.dropIcon}>📸</div>
            <p className={styles.dropTitle}>
              Drop an image or <span className="text-amber">click to browse</span>
            </p>
            <p className={`${styles.dropHint} text-tertiary text-sm`}>
              JPG, PNG, or WebP · Max 10 MB
            </p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp"
            onChange={handleChange}
            className="sr-only"
          />
        </div>
      ) : (
        <div className={styles.previewContainer}>
          <div className={styles.previewImgWrap}>
            <img src={preview} alt="Selected" className={styles.previewImg} />
          </div>
          <div className={styles.previewInfo}>
            <span className={`text-sm ${styles.fileName}`}>{fileName}</span>
            <button
              className="btn btn-ghost btn-sm"
              onClick={handleRemove}
            >
              ✕ Remove
            </button>
          </div>
        </div>
      )}

      {error && <p className="form-error mt-2">{error}</p>}
    </div>
  );
}
