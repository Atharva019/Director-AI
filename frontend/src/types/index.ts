// ─── User ───────────────────────────────────────────────────────────────────
export interface User {
  id: number;
  firebase_uid: string;
  email: string;
  display_name: string;
  avatar_url: string | null;
  created_at: string;
}

// ─── Project ────────────────────────────────────────────────────────────────
export type ProjectStatus = "draft" | "in_production" | "completed";
export type Genre =
  | "Drama"
  | "Action"
  | "Comedy"
  | "Horror"
  | "Thriller"
  | "Sci-Fi"
  | "Documentary"
  | "Romance"
  | "Other";

export interface Project {
  id: number;
  title: string;
  description: string | null;
  genre: Genre | string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  scenes_count: number;
}

// ─── Scene ──────────────────────────────────────────────────────────────────
export type LocationType = "interior" | "exterior" | "both";
export type TimeOfDay = "dawn" | "morning" | "day" | "afternoon" | "golden_hour" | "dusk" | "night";

export interface Scene {
  id: number;
  project_id: number;
  scene_number: number;
  title: string;
  description: string | null;
  location_type: LocationType;
  time_of_day: TimeOfDay;
  mood: string | null;
  notes: string | null;
  shots_count: number;
}

// ─── Shot ───────────────────────────────────────────────────────────────────
export type ShotType =
  | "wide"
  | "medium"
  | "close-up"
  | "extreme_close-up"
  | "over_the_shoulder"
  | "pov"
  | "aerial"
  | "establishing"
  | "insert"
  | "two_shot";

export type CameraAngle =
  | "eye_level"
  | "low_angle"
  | "high_angle"
  | "dutch_angle"
  | "birds_eye"
  | "worms_eye";

export type CameraMovement =
  | "static"
  | "pan"
  | "tilt"
  | "dolly"
  | "tracking"
  | "crane"
  | "handheld"
  | "steadicam"
  | "zoom";

export interface Shot {
  id: number;
  scene_id: number;
  shot_number: number;
  shot_type: ShotType | string;
  camera_angle: CameraAngle | string;
  camera_movement: CameraMovement | string;
  lens_mm: number | null;
  description: string | null;
  notes: string | null;
}

// ─── Analysis ───────────────────────────────────────────────────────────────
export interface AnalysisResult {
  lighting_setup: string;
  color_temperature: string;
  lighting_style: string;
  lighting_ratio: string;
  estimated_focal_length: string;
  estimated_aperture: string;
  depth_of_field: string;
  camera_height: string;
  camera_angle: string;
  composition_rules: string[];
  framing: string;
  aspect_ratio: string;
  dominant_colors: string[];
  color_palette_mood: string;
  overall_mood: string;
  recommended_equipment: string[];
  setup_instructions: string[];
  tips: string[];
  confidence_score: number;
  model_used: string;
}

export interface AnalysisSceneRef {
  id: string | number;
  scene_number: number;
  title: string;
}

export interface SceneAnalysis {
  id: number;
  scene_id: number | null;
  scene?: AnalysisSceneRef | null;
  user_id: number;
  image_path: string;
  analysis_result: AnalysisResult;
  model_used: string;
  confidence_score: number;
  created_at: string;
}

// ─── API Response Wrappers ──────────────────────────────────────────────────
export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
