"""Deterministic CadQuery builders for the supported concept gearbox."""

import os
import tempfile
from pathlib import Path

# ezdxf is imported by CadQuery exporters and otherwise tries to cache fonts in
# the user home. A system temporary cache keeps CLI runs writable and isolated.
os.environ.setdefault(
    'XDG_CACHE_HOME', str(Path(tempfile.gettempdir()) / 'gearen-cache')
)

from gearen.cad.assembly import build_gearbox_assembly

__all__ = ["build_gearbox_assembly"]
