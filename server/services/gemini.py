"""
QuickLab — Secure Google Gemini AI Service
Uses the official google-genai SDK to interact with Gemini models.
The API key is strictly read from GEMINI_API_KEY environment variable.
Never leaks keys, system paths, or raw internal exceptions to clients.
"""

import os
import logging
from typing import Optional, Dict, Any

from server.config import settings

logger = logging.getLogger("quicklab.gemini")


class GeminiService:
    def __init__(self):
        self._client = None

    @property
    def api_key(self) -> Optional[str]:
        return os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY

    @property
    def model_name(self) -> str:
        return os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-1.5-flash"

    def is_configured(self) -> bool:
        """Returns True if GEMINI_API_KEY is present and non-empty."""
        key = self.api_key
        return bool(key and key.strip())

    def _get_client(self):
        """Initializes and returns the google-genai Client."""
        if not self.is_configured():
            return None
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize google-genai client: {e}")
                return None
        return self._client

    def generate_chat_response(self, message: str, system_instruction: Optional[str] = None) -> str:
        """
        Sends message to Gemini and returns generated text.
        Never leaks API keys, sensitive tokens, or internal tracebacks.
        """
        if not self.is_configured():
            raise ValueError("GEMINI_API_KEY is not configured on this server.")

        client = self._get_client()
        if not client:
            raise RuntimeError("AI service is temporarily unavailable.")

        try:
            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=self.model_name,
                contents=message,
                config=config if config else None
            )

            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
            return "No response generated from AI."

        except Exception as e:
            # Log exact error server-side, never expose internal exception details to client
            logger.error(f"Gemini API execution error: {str(e)}", exc_info=True)
            raise RuntimeError("AI service is temporarily unavailable.")

    def explain_code(self, code: str, context: Optional[str] = None) -> str:
        """Explains Python code concisely with attention to the 7 QuickLab scientific libraries."""
        system_instruction = (
            "You are QuickLab AI, an expert Python, data science, and machine learning assistant. "
            "Explain Python code clearly, concisely, and accurately. "
            "Highlight data structures, scientific operations (NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, Scikit-learn), "
            "and expected outputs in clean GitHub-flavored markdown."
        )
        prompt = f"Please explain this Python code concisely:\n\n```python\n{code}\n```"
        if context:
            prompt += f"\n\nContext:\n{context}"
        return self.generate_chat_response(prompt, system_instruction=system_instruction)

    def fix_error(self, code: str, error: str) -> str:
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
        return self.generate_chat_response(prompt, system_instruction=system_instruction)

    def generate_code(self, user_prompt: str) -> str:
        """Generates clean Python code using the 7 supported libraries from user instructions."""
        system_instruction = (
            "You are QuickLab AI, an expert Python code generator. "
            "Generate clean, runnable Python 3.11 code using the standard QuickLab scientific libraries: "
            "NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, and Scikit-learn. "
            "Always output the Python code in a ```python ``` block with helpful comments."
        )
        prompt = f"Write Python code to accomplish the following task:\n\n{user_prompt}"
        return self.generate_chat_response(prompt, system_instruction=system_instruction)


gemini_service = GeminiService()
