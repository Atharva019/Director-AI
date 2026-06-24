"""
Scene analysis orchestrator – validates image, encodes to base64,
sends to Ollama with a structured cinematography prompt, and parses
the response into a typed AnalysisResult dict.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from services.gemini_service import GeminiService
from utils.prompts import SCENE_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

# Keys expected in the structured analysis output.
EXPECTED_KEYS = [
    "lighting_setup",
    "color_temperature",
    "lighting_style",
    "lighting_ratio",
    "estimated_focal_length",
    "estimated_aperture",
    "depth_of_field",
    "camera_height",
    "camera_angle",
    "composition_rules",
    "framing",
    "aspect_ratio",
    "dominant_colors",
    "color_palette_mood",
    "overall_mood",
    "recommended_equipment",
    "setup_instructions",
    "tips",
]


class SceneAnalyzer:
    """Orchestrates AI-powered analysis of film stills and reference images."""

    def __init__(self, ai_client: Optional[GeminiService] = None) -> None:
        self.ai_client = ai_client or GeminiService()

    # ── Public API ────────────────────────────────────────────────────────

    async def analyze(
        self,
        image_path: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a film still / reference image.

        Parameters
        ----------
        image_path : str
            Absolute or relative path to the image on disk.
        model : str, optional
            Override the default Ollama model.

        Returns
        -------
        dict
            Structured analysis result including all cinematography fields
            plus ``confidence_score`` and ``model_used``.

        Raises
        ------
        FileNotFoundError
            If the image_path does not exist.
        ValueError
            If the file cannot be read or encoded.
        """
        # 1. Validate the file exists
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # 2. Read and encode to base64
        image_bytes = path.read_bytes()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # 3. Send to Gemini
        logger.info("Sending image %s to Gemini for analysis (model=%s)", path.name, model or "default")
        response = await self.ai_client.analyze_image(
            image_base64=image_b64,
            prompt=SCENE_ANALYSIS_PROMPT,
            model=model,
        )

        # 4. Parse response
        raw_text: str = response.get("response", "")
        model_used: str = response.get("model", model or self.ai_client.default_model)

        analysis = self._parse_response(raw_text)
        analysis["model_used"] = model_used

        # If the model didn't include a confidence score, infer one from key coverage.
        if "confidence_score" not in analysis or not isinstance(analysis.get("confidence_score"), (int, float)):
            analysis["confidence_score"] = self._compute_confidence(analysis)

        return analysis

    # ── Internal helpers ──────────────────────────────────────────────────

    def _parse_response(self, raw: str) -> Dict[str, Any]:
        """
        Try to extract a JSON object from the model's raw text output.
        Falls back to returning the raw text wrapped in a dict.
        """
        # Try to find a JSON block in the response
        # Models sometimes wrap JSON in ```json ... ``` fences
        cleaned = raw.strip()

        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        # Attempt direct JSON parse
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Try to find JSON within the text (first { to last })
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(cleaned[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        # Fallback: return raw text as a partial result
        logger.warning("Could not parse structured JSON from Gemini response; returning raw text.")
        return {
            "raw_response": raw,
            "lighting_setup": "",
            "color_temperature": "",
            "lighting_style": "",
            "lighting_ratio": "",
            "estimated_focal_length": "",
            "estimated_aperture": "",
            "depth_of_field": "",
            "camera_height": "",
            "camera_angle": "",
            "composition_rules": [],
            "framing": "",
            "aspect_ratio": "",
            "dominant_colors": [],
            "color_palette_mood": "",
            "overall_mood": "",
            "recommended_equipment": [],
            "setup_instructions": [],
            "tips": [],
        }

    def _compute_confidence(self, analysis: Dict[str, Any]) -> float:
        """
        Heuristic confidence score based on how many expected keys
        are present and non-empty in the analysis result.
        """
        filled = 0
        for key in EXPECTED_KEYS:
            val = analysis.get(key)
            if val and val != "" and val != []:
                filled += 1
        return round(filled / len(EXPECTED_KEYS), 2)
