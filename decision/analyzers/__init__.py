"""Decision Engine — session analyzers.

SessionAnalyzer extracts time-window information from Activity Events
so that rules do not need to scan events themselves.
"""

from decision.analyzers.session import SessionAnalyzer

__all__ = ["SessionAnalyzer"]
