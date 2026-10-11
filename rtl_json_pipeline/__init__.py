"""Spec-only structured design and verification pipeline."""
import sys
from pathlib import Path
_dependencies = Path(__file__).resolve().parents[1] / '.deps' / 'json_pipeline'
if _dependencies.is_dir():
    sys.path.insert(0, str(_dependencies))
