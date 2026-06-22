"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import styles from "./Navbar.module.css";

export default function Navbar() {
  const { user, firebaseUser, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const displayName =
    user?.display_name ?? firebaseUser?.displayName ?? "User";
  const avatarUrl =
    user?.avatar_url ?? firebaseUser?.photoURL ?? null;

  return (
    <nav className={styles.nav}>
      <div className={`container ${styles.inner}`}>
        {/* Logo */}
        <Link href="/dashboard" className={styles.logo}>
          <span className={styles.logoIcon}>🎬</span>
          <span className={styles.logoText}>
            Director <span className="text-gradient">AI</span>
          </span>
        </Link>

        {/* Desktop links */}
        <div className={styles.links}>
          <Link href="/dashboard" className={styles.link}>
            Dashboard
          </Link>
          <Link href="/analyze" className={styles.link}>
            Analyze
          </Link>
          <Link href="/history" className={styles.link}>
            History
          </Link>
        </div>

        {/* User section */}
        <div className={styles.user}>
          <div className={styles.avatar}>
            {avatarUrl ? (
              <img src={avatarUrl} alt={displayName} />
            ) : (
              <span>{displayName[0]?.toUpperCase()}</span>
            )}
          </div>
          <span className={`${styles.displayName} hide-mobile`}>
            {displayName}
          </span>
          <button onClick={signOut} className={`btn btn-ghost btn-sm ${styles.signOut}`}>
            Sign Out
          </button>
        </div>

        {/* Mobile hamburger */}
        <button
          className={styles.hamburger}
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          <span className={`${styles.bar} ${menuOpen ? styles.barOpen1 : ""}`} />
          <span className={`${styles.bar} ${menuOpen ? styles.barOpen2 : ""}`} />
          <span className={`${styles.bar} ${menuOpen ? styles.barOpen3 : ""}`} />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className={styles.mobileMenu}>
          <Link href="/dashboard" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
            Dashboard
          </Link>
          <Link href="/analyze" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
            Analyze
          </Link>
          <Link href="/history" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
            History
          </Link>
          <hr className="divider" />
          <button onClick={signOut} className="btn btn-ghost" style={{ width: "100%" }}>
            Sign Out
          </button>
        </div>
      )}
    </nav>
  );
}
