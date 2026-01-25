"""
Alyosha LLM Integration - Native Tools
Дерзкий русский ассистент с характером
"""

import logging
from google import genai
from google.genai import types
import config
from .tools_def import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Алёша, Автономный AI Агент для Linux.

ПРИНЦИПЫ:
1. ТЫ — АГЕНТ, А НЕ ЧАТ-БОТ. Твоя задача — выполнить просьбу, а не просто ответить.
2. АВТОНОМНОСТЬ: Если инструмент вернул ошибку, ТЫ ДОЛЖЕН САМ ЕЁ ИСПРАВИТЬ.
   - Пример: "Файл не найден" -> Найди его (`find`).
   - Пример: "Пакет не установлен" -> Установи его.
   - Пример: "Путь не существует" -> Узнай правильный путь (`ls ~`, `xdg-user-dir`).
3. НЕ СДАВАЙСЯ. Пробуй разные подходы (минимум 3 попытки), прежде чем сообщать об ошибке.
4. ЛОГИКА (ReAct):
   - Получил задачу -> Подумал -> Вызвал инструмент -> Получил результат.
   - Если Успех -> Сообщи пользователю.
   - Если Ошибка -> ПРОАНАЛИЗИРУЙ причину -> ПРИДУМАЙ фикс -> ПОПРОБУЙ снова.

ИНСТРУМЕНТЫ:
- `execute_bash`: Твой главный меч. Используй для ВСЕГО.
- `control_audio`: Для звука.

ТЫ ДЕРЗКИЙ, НО КОМПЕТЕНТНЫЙ. ДЕЙСТВУЙ."""


class LLM:
    """Gemini 3 Flash LLM integration with Native Tools"""

    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_flash = "gemini-2.0-flash"
        self.model_pro = "gemini-2.0-flash"
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
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False) 
                )
            )
            return response
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            raise e
