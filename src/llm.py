"""
Alyosha LLM Integration - Native Tools
Дерзкий русский ассистент с характером
"""

import logging
from google import genai
from google.genai import types
import config
from .tools_def import TOOL_DEFINITIONS
import advanced_prompt

logger = logging.getLogger(__name__)


# Technical Context (Agent Capabilities)

# Link directly to advanced_prompt
SYSTEM_PROMPT = advanced_prompt.SYSTEM_PROMPT


class LLM:
    """Gemini 3 Flash LLM integration with Native Tools"""

    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_flash = "gemini-3-flash-preview"
        self.model_pro = "gemini-3-pro-preview"
        self.forced_model = None
        self.active_model = self.model_flash

    def chat(
        self,
        user_message: str,
        context: list[dict],
        image_path: str = "",
        user_profile: str = "",
    ) -> types.GenerateContentResponse:
        """
        Отправить сообщение и получить RAW ответ (для обработки Tool Call снаружи)
        Returns: types.GenerateContentResponse object directly
        """
        # Determine model
        model_name = self.model_flash

        # Build conversation history
        contents = []

        # Determine history (exclude current message if already in context to avoid duplication)
        history = context
        if (
            context
            and context[-1]["content"] == user_message
            and context[-1]["role"] == "user"
        ):
            history = context[:-1]

        for msg in history[-config.MAX_CONTEXT_MESSAGES :]:
            # Map roles to Gemini API roles ('user' -> 'user', 'assistant' -> 'model')
            role = "user" if msg["role"] == "user" else "model"

            # If message has function calls or responses, we need to handle them carefully
            # For simplicity in this v1 refactor, we usually only pass text history.
            # Complex history reconstruction with tools is tricky.
            # We'll stick to text history for now.
            contents.append(
                types.Content(
                    role=role, parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        current_parts = [types.Part.from_text(text=user_message)]
        if image_path:
            try:
                from pathlib import Path

                img_data = Path(image_path).read_bytes()
                current_parts.append(
                    types.Part.from_bytes(data=img_data, mime_type="image/png")
                )
            except Exception as e:
                logger.error(f"Error loading image: {e}")

        contents.append(types.Content(role="user", parts=current_parts))

        # Prepare Tools
        # Native Function Calling (pass list of callables directly)
        tools = TOOL_DEFINITIONS

        # System Instruction
        system_instruction = SYSTEM_PROMPT
        if user_profile:
            system_instruction += f"\n\nПРОФИЛЬ ЮЗЕРА:\n{user_profile}"

        try:
            # Native Tool Use Call
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    tools=tools,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=False
                    ),
                ),
            )
            return response
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            raise e
