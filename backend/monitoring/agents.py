"""
Backward-compatibility shim.

The LogAnalysisAgent has been moved to monitoring.agent.agent.
This module re-exports it so existing imports are unaffected:

    from monitoring.agents import LogAnalysisAgent  # still works
"""

from monitoring.agent.agent import LogAnalysisAgent

__all__ = ["LogAnalysisAgent"]
