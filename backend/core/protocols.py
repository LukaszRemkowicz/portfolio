from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class TranslationAgentProtocol(Protocol):
    """
    Protocol defining the interface for a translation agent.
    """

    def translate_place(self, text: str, target_lang_code: str, country_name: str) -> Optional[str]:
        """
        Translates a place name with country context.
        """
        ...

    def translate_tag(self, text: str, target_lang_code: str) -> Optional[str]:
        """
        Translates a technical or descriptive tag.
        """
        ...

    def translate(self, text: str, target_lang_code: str) -> Optional[str]:
        """
        Translates plain text.
        """
        ...

    def translate_html(self, text: str, target_lang_code: str) -> Optional[str]:
        """
        Translates HTML content, preserving tags.
        """
        ...
