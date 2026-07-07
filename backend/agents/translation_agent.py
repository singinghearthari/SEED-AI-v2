"""
SEED AI — Translation Agent (Production)
Translates agricultural advice into the farmer's preferred language.
Returns structured AgentResult — never fakes success.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent


class TranslationResult(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


class TranslationAgent(BaseAgent):

    def __init__(self):
        super().__init__("Translation")

    def _process(self, context: Dict[str, Any]) -> tuple:
        target_lang = context.get("target_language", "en")
        text = context.get("text", "")
        self.log_execution(f"Translating to {target_lang}")

        if not text:
            raise ValueError("No text provided for translation")

        if target_lang == "en":
            return (
                {
                    "original_text": text,
                    "translated_text": text,
                    "source_language": "en",
                    "target_language": "en",
                },
                [],
                0,
                100.0,
                "No translation needed (already English).",
            )

        prompt = f"""
Translate the following agricultural advisory text to {target_lang}.
Preserve all technical farming terms, chemical names, and measurements.

Text to translate:
{text}

Return the original text, translated text, source language code, and target language code.
"""
        response = self.call_llm(prompt, schema=TranslationResult)
        result = TranslationResult.model_validate_json(response.text)
        tokens = response.total_tokens

        return (
            result.model_dump(),
            ["Gemini Translation"],
            tokens,
            90.0,
            f"Translated from {result.source_language} to {result.target_language}",
        )
