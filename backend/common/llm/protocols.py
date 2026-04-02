from typing import Protocol, runtime_checkable


@runtime_checkable
class TranslationAgentProtocol(Protocol):
    """
    Protocol defining the interface for a translation agent.
    """

    def translate_place(self, text: str, target_lang_code: str, country_name: str) -> str | None:
        """
        Translates a place name with country context.
        """
        ...

    def translate_tag(self, text: str, target_lang_code: str) -> str | None:
        """
        Translates a technical or descriptive tag.
        """
        ...

    def translate(self, text: str, target_lang_code: str, field_hint: str = "") -> str | None:
        """
        Translates plain text.
        """
        ...

    def translate_html(self, text: str, target_lang_code: str, field_hint: str = "") -> str | None:
        """
        Translates HTML content, preserving tags.
        """
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers (GPT, Gemini, Claude, etc.)."""

    def ask_question(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str | None:
        """
        Ask the LLM a question with system and user prompts.

        Args:
            system_prompt: System-level instructions
            user_message: User's actual content/question
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            LLM's response text, or None on failure
        """
        ...

    def ask_question_with_usage(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> tuple[str | None, dict]:
        """
        Ask the LLM a question and return response + usage stats.

        Returns:
            Tuple of (response_text, usage_dict)
        """
        ...
