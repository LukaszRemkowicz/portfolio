"""
monitoring.agent package.

Re-exports LogAnalysisAgent so existing imports continue to work:
    from monitoring.agent import LogAnalysisAgent
"""

from monitoring.agent.agent import LogAnalysisAgent

__all__ = ["LogAnalysisAgent"]
