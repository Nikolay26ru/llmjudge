"""Single source of truth for the package version.

Read by ``pyproject.toml`` (hatchling dynamic version) and by the call cache
key, so the two never drift.
"""

from __future__ import annotations

__version__ = "0.1.1"
