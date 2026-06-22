import { initializeApp, getApps, getApp, type FirebaseApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  signOut,
  onAuthStateChanged,
  type Auth,
  type User,
  type Unsubscribe,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN ?? "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET ?? "",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID ?? "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID ?? "",
};

// ─── Lazy initialization ────────────────────────────────────────────────────
// Firebase is only initialized at runtime in the browser to avoid crashes
// during Next.js static page generation when env vars aren't set.

let _app: FirebaseApp | null = null;
let _auth: Auth | null = null;

function getFirebaseApp(): FirebaseApp {
  if (!_app) {
    _app = getApps().length ? getApp() : initializeApp(firebaseConfig);
  }
  return _app;
}

function getFirebaseAuth(): Auth {
  if (!_auth) {
    _auth = getAuth(getFirebaseApp());
  }
  return _auth;
}

// Proxy object so existing `auth.currentUser` references keep working
export const auth: Auth = new Proxy({} as Auth, {
  get(_target, prop) {
    if (typeof window === "undefined") {
      // During SSR, return safe defaults
      if (prop === "currentUser") return null;
      if (prop === "onAuthStateChanged") return () => () => {};
      return undefined;
    }
    const realAuth = getFirebaseAuth();
    const value = (realAuth as unknown as Record<string | symbol, unknown>)[prop];
    return typeof value === "function" ? value.bind(realAuth) : value;
  },
});

export const app = new Proxy({} as FirebaseApp, {
  get(_target, prop) {
    if (typeof window === "undefined") return undefined;
    const realApp = getFirebaseApp();
    const value = (realApp as unknown as Record<string | symbol, unknown>)[prop];
    return typeof value === "function" ? value.bind(realApp) : value;
  },
});

// ─── Auth helpers ───────────────────────────────────────────────────────────

const googleProvider = new GoogleAuthProvider();

export async function signInWithGoogle() {
  return signInWithPopup(getFirebaseAuth(), googleProvider);
}

export async function signInWithEmail(email: string, password: string) {
  return signInWithEmailAndPassword(getFirebaseAuth(), email, password);
}

export async function signUpWithEmail(
  email: string,
  password: string,
  displayName: string
) {
  const cred = await createUserWithEmailAndPassword(getFirebaseAuth(), email, password);
  await updateProfile(cred.user, { displayName });
  return cred;
}

export async function signOutUser() {
  return signOut(getFirebaseAuth());
}

export function onAuthChange(callback: (user: User | null) => void): Unsubscribe {
  if (typeof window === "undefined") {
    // SSR: no-op, call back with null immediately
    callback(null);
    return () => {};
  }
  return onAuthStateChanged(getFirebaseAuth(), callback);
}
