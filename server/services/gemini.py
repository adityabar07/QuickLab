"""
QuickLab — Secure Google Gemini AI Service
Communicates with Google Generative Language API from the FastAPI backend.
The GEMINI_API_KEY remains strictly secret on the server and is never sent to the client.
"""

import logging
import httpx
from typing import Dict, Any, Optional
from server.config import settings

logger = logging.getLogger("quicklab.gemini")

GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL

    def is_configured(self) -> bool:
        """Returns True if GEMINI_API_KEY is present and non-empty."""
        return bool(self.api_key and self.api_key.strip())

    async def _call_gemini(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Calls Google Gemini REST API safely using httpx."""
        if not self.is_configured():
            raise ValueError(
                "Gemini AI is not configured on this QuickLab server. "
                "Please configure GEMINI_API_KEY in the backend environment variables."
            )

        url = f"{GEMINI_API_ENDPOINT}/{self.model}:generateContent?key={self.api_key}"

        contents = [{"parts": [{"text": prompt}]}]
        payload: Dict[str, Any] = {"contents": contents}

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        payload["generationConfig"] = {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                    return "No response generated from Gemini."

                elif response.status_code == 429:
                    logger.warning("Gemini API rate limit exceeded.")
                    raise RuntimeError("Gemini API quota or rate limit exceeded. Please try again shortly.")

                elif response.status_code in (400, 403):
                    logger.error(f"Gemini API authentication/bad request error: HTTP {response.status_code}")
                    raise ValueError("Gemini API key is invalid or unauthorized.")

                else:
                    logger.error(f"Gemini API responded with status {response.status_code}")
                    raise RuntimeError("Unable to communicate with the Gemini AI service.")

        except httpx.TimeoutException:
            logger.error("Gemini API request timed out.")
            raise RuntimeError("Gemini AI request timed out. Please try again.")

        except (ValueError, RuntimeError):
            raise

        except Exception as e:
            # Log exact error server-side, never expose internal tracebacks to client
            logger.error(f"Unexpected error calling Gemini API: {str(e)}", exc_info=True)
            raise RuntimeError("An error occurred while contacting the Gemini AI service.")

    async def explain_code(self, code: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Explains Python code concisely with attention to scientific libraries (NumPy, Pandas, etc.)."""
        system_instruction = (
            "You are QuickLab AI, an expert Python data science and machine learning assistant. "
            "Explain Python code clearly, concisely, and accurately. "
            "Highlight data structures, scientific operations (NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, Scikit-learn), "
            "and expected outputs in clean GitHub-flavored markdown."
        )

        prompt = f"Please explain this Python code concisely:\n\n```python\n{code}\n```"
        if context:
            prompt += f"\n\nContext:\n{context}"

        explanation = await self._call_gemini(prompt, system_instruction=system_instruction)
        return {"explanation": explanation}

    async def fix_error(self, code: str, error: str) -> Dict[str, Any]:
        """Analyzes a Python error traceback and provides explanation and corrected code."""
        system_instruction = (
            "You are QuickLab AI, a Python debugging assistant. "
            "When given Python code and an error message/traceback: "
            "1. Explain what caused the error concisely. "
            "2. Provide the corrected Python code in a single ```python ``` block. "
            "Keep explanations brief, precise, and practical."
        )

        prompt = (
            f"Here is the Python code that failed:\n```python\n{code}\n```\n\n"
            f"Error / Traceback:\n```\n{error}\n```\n\n"
            f"Please explain the root cause and provide the exact fixed code."
        )

        fix_response = await self._call_gemini(prompt, system_instruction=system_instruction)
        return {"fix": fix_response}

    async def generate_code(self, user_prompt: str) -> Dict[str, Any]:
        """Generates clean Python code using the 7 supported libraries from user instructions."""
        system_instruction = (
            "You are QuickLab AI, an expert Python code generator. "
            "Generate clean, runnable Python 3.11 code using the standard QuickLab scientific libraries: "
            "NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, and Scikit-learn. "
            "Always output the Python code in a ```python ``` block with helpful comments."
        )

        prompt = f"Write Python code to accomplish the following task:\n\n{user_prompt}"
        generated = await self._call_gemini(prompt, system_instruction=system_instruction)
        return {"code": generated}


gemini_service = GeminiService()
