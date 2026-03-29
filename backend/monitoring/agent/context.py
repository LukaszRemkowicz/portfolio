"""
Prompt context strings for the LogAnalysisAgent loaded from prompt assets.

Each constant is a self-contained piece of context. Skills compose these
into full system prompts. The source of truth lives under
`backend/monitoring/agent_assets/`.
"""

from monitoring.prompt_assets import PromptAssetLoader

_loader: PromptAssetLoader = PromptAssetLoader()

PROJECT_CONTEXT = _loader.load_text("skills/project_context.md")
NORMAL_PATTERNS_CONTEXT = _loader.load_text("skills/normal_patterns.md")
APPLICATION_MONITORING_CONTEXT = _loader.load_text("skills/application_monitoring.md")
BOT_DETECTION_CONTEXT = _loader.load_text("skills/bot_detection.md")
OWASP_SECURITY_CONTEXT = _loader.load_text("skills/owasp_security.md")
SEVERITY_GUIDE = _loader.load_text("skills/severity_guide.md")
RECOMMENDATIONS_GUIDE = _loader.load_text("skills/recommendations_guide.md")
HISTORICAL_CONTEXT = _loader.load_text("skills/historical_context.md")
RESPONSE_FORMAT = _loader.load_text("prompts/monitoring_log_response_format.md")
