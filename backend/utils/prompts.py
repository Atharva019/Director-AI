"""
Prompt templates for AI-powered cinematography analysis.

All prompts instruct the model to return structured JSON so that the
results can be reliably parsed downstream.

The compressed prompt uses ~400 tokens (vs ~1,200 for the verbose
version), significantly reducing token usage per analysis request.
"""

SCENE_ANALYSIS_PROMPT: str = """Expert cinematographer: analyze this film still. Return ONLY a valid JSON object with these exact keys:

{
  "lighting_setup": "<key/fill/back/rim positions, motivated or artificial, grip terminology>",
  "color_temperature": "<Kelvin estimate, gels/filtration>",
  "lighting_style": "<high-key/low-key/chiaroscuro/noir/naturalistic/etc>",
  "lighting_ratio": "<key:fill ratio e.g. '4:1 dramatic'>",
  "estimated_focal_length": "<mm, consider distortion and compression>",
  "estimated_aperture": "<f-stop based on DoF>",
  "depth_of_field": "<shallow/moderate/deep, what's in/out of focus>",
  "camera_height": "<low/eye-level/high/overhead>",
  "camera_angle": "<straight/Dutch/OTS/POV/profile/three-quarter>",
  "composition_rules": ["<rule of thirds, leading lines, symmetry, etc>"],
  "framing": "<ECU/CU/MCU/MS/MWS/WS/EWS/two-shot/OTS>",
  "aspect_ratio": "<e.g. 2.39:1 Scope, 1.78:1 16:9>",
  "dominant_colors": ["<3-5 descriptive color names>"],
  "color_palette_mood": "<warm/cool, saturated/desat, palette type and mood contribution>",
  "overall_mood": "<emotional tone: tense, serene, intimate, epic, etc>",
  "recommended_equipment": ["<specific camera, lenses, lighting units, grip gear>"],
  "setup_instructions": ["<step-by-step recreation: lights, camera, lens, rigging>"],
  "tips": ["<pro insights, common mistakes, budget alternatives>"],
  "confidence_score": 0.85
}

Rules: Use professional cinematography terms. Be specific ('85mm at f/2' not 'telephoto'). confidence_score 0.0–1.0. No text outside the JSON object."""
